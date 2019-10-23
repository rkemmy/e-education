import datetime
from django.db import transaction
from rest_framework import serializers
from education.eneza.models import VideoTutorial, Question, MultiChoiceQuestion,\
        FreeFormQuestion, Quiz, MultiChoiceQuestionChoice, SubmittedSolution,\
        SubmittedSolutionActivity, SubmittedAnswer, SubmittedFreeformAnswer,SubmittedMultichoiceAnswer


class AbstractSerializersMixin:

    @transaction.atomic
    def create(self, validated_data):
        if self.context["request"].user:
            validated_data["created_by"]=self.context["request"].user
        return super().create(validated_data)
    @transaction.atomic
    def update(self, instance, validated_data):
        if self.context["request"].user:
            validated_data["updated_by"]=self.context["request"].user
        return super().updated(instance, validated_data)


def create_private_field(serializer_class,field_name):
    class PrivateField(serializer_class):
        def get_attribute(self, obj):
            # We pass the object instance onto `to_representation`,
            # not just the field attribute.
            return obj

        def to_representation(self, obj):
            # for read functionality
            if obj.created_by != self.context['request'].user:
                return None
            else:
                return getattr(obj,field_name)
    return PrivateField

class VideoTutorialSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    def validate(self, data):
        print(data["video"].__dict__)
        size = data["video"].size
        if size > VideoTutorial.MAX_VIDEO_UPLOAD_SIZE:
            raise serializers.ValidationError("Max upload size is %s"%str(VideoTutorial.MAX_VIDEO_UPLOAD_SIZE))
        return data

    class Meta:
        model = VideoTutorial
        fields = "__all__"

class QuizSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    def save(self, *args, **kwargs):
        validated_data = self.validated_data
        video_tutorial = validated_data["video_tutorial"]
        if video_tutorial.created_by  != self.context["request"].user:
            raise serializers.ValidationError("Invalid Permissions")
        return super().save(**kwargs)

    class Meta:
        model = Quiz
        fields = "__all__"


class QuestionsSerializerMixin:
    def validate(self, data):
        if not self.partial:
            quiz, position = data["quiz"], data["position"]
        if self.partial:
            quiz=self.instance.quiz
            position=self.instance.position
            s=[quiz,position]
            for i,f in enumerate(["quiz","position"]):
                if f in data.keys():
                    s[i]=data[f]
            quiz,position=s[0],s[1]
            question = Question.objects.filter(quiz_id=quiz, position=position)
            if question:
                if question[0].id != self.instance.question_ptr_id:
                    raise serializers.ValidationError("Unique together constraint quiz_position violated")
                return data
        question = Question.objects.filter(quiz_id=quiz, position=position)
        if question:
            raise serializers.ValidationError("Unique together constraint quiz_position violated")
        return data

    def save(self,**kwargs):
        validated_data =  self.validated_data
        instance =  self.instance
        if instance:
            quiz =  instance.quiz
        else:
            quiz = validated_data["quiz"]
        if quiz.created_by != self.context["request"].user:
            raise serializers.ValidationError("Invalid Permissions")
        return super().save(**kwargs)


class QuestionSerializer(AbstractSerializersMixin, QuestionsSerializerMixin, serializers.ModelSerializer):

    def validate(self, data):
        if not self.partial:
            quiz, position = data["quiz"], data["position"]
        if self.partial:
            quiz=self.instance.quiz
            position=self.instance.position
            s=[quiz,position]
            for i,f in enumerate(["quiz","position"]):
                if f in data.keys():
                    s[i]=data[f]
            quiz,position=s[0],s[1]
        question = Question.objects.filter(quiz_id=quiz, position=position)
        if question:
            raise serializers.ValidationError("Unique together constraint quiz_position violated")
        return data

    class Meta:
        model = Question
        fields = "__all__"

class MultiChoiceQuestionChoiceSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    answer = create_private_field(serializers.BooleanField,"answer")()

    def validate(self, data):
        if data["question"].created_by != self.context["request"].user and not self.context["request"].user.is_superuser:
            raise serializers.ValidationError("Invalid Permissions")
        if not self.partial:
            position, question = data["position"], data["question"]
            choice = MultiChoiceQuestionChoice.objects.filter(position=position, question=question)
            if choice:
                raise serializers.ValidationError("Unique together constraint question_position violated")
        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        instance =  self.instance
        if instance:
            question = self.instance.question
        else:
            question = validated_data["question"]
        if question.created_by != self.context["request"].user:
            raise serializers.ValidationError("Invalid Permisssions")
        return super().save(**kwargs)


    class Meta:
        model = MultiChoiceQuestionChoice
        fields = "__all__"

class MultiChoiceQuestionSerializer(AbstractSerializersMixin, QuestionsSerializerMixin, serializers.ModelSerializer):

    choices = MultiChoiceQuestionChoiceSerializer(many=True, read_only=True)
    question_type = serializers.CharField(read_only=True,)

    @transaction.atomic
    def create(self,validated_data):
        validated_data["question_type"] = Question.MULTI_CHOICE_QUESTION_TYPE
        return super().create(validated_data)

    class Meta:
        model = MultiChoiceQuestion
        fields = "__all__"


class FreeFormQuestionSerializer(AbstractSerializersMixin, QuestionsSerializerMixin, serializers.ModelSerializer):
    question_type = serializers.CharField(read_only=True,)
    answer = create_private_field(serializers.CharField,"answer")()

    @transaction.atomic
    def create(self,validated_data):
        validated_data["question_type"] = Question.FREE_FORM_QUESTION_TYPE
        return super().create(validated_data)

    class Meta:
        model = FreeFormQuestion
        fields = "__all__"

class SubmittedSolutionSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    start = serializers.ReadOnlyField()
    stop = serializers.ReadOnlyField()

    @transaction.atomic
    def create(self,validated_data):
        validated_data["start"]=datetime.datetime.utcnow()
        return super().create(validated_data)

    class Meta:
        model = SubmittedSolution
        fields = "__all__"


class SubmittedMultichoiceAnswerSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    class Meta:
        model = SubmittedMultichoiceAnswer
        fields = "__all__"

class SubmittedFreeformAnswerSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    class Meta:
        model = SubmittedFreeformAnswer
        fields = "__all__"


class SubmittedAnswerSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    class Meta:
        model = SubmittedAnswer
        fields = "__all__"
