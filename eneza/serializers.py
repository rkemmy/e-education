import datetime
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from eneza.models import VideoTutorial, Question, MultiChoiceQuestion,\
        FreeFormQuestion, Quiz, MultiChoiceQuestionChoice, QuizSolution,\
        QuizSolutionActivity, SubmittedFreeformAnswer,SubmittedMultichoiceAnswer
    
from eneza.exceptions import InvalidPermissionsException, SimpleValidationError

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import pytz
from eneza.services.utils import strfdelta




class AbstractSerializersMixin:
   
    @transaction.atomic
    def create(self, validated_data):
        if self.context["request"].user:
            validated_data["created_by"]=self.context["request"].user
        print(validated_data)
        return super().create(validated_data)
    @transaction.atomic
    def update(self, instance, validated_data):
        if self.context["request"].user:
            validated_data["updated_by"]=self.context["request"].user
        return super().update(instance, validated_data)

class AbstractModelSerializerMeta:
    DEFAULT_FIELDS = ["id","created_by","updated_by","is_active","created_at","updated_at"]
    read_ony_fields = ["created_by","updated_by","created_at","updated_at","is_active"]

def create_private_field(serializer_class,field_name):
    class PrivateField(serializer_class):
        def get_attribute(self, obj):
            return obj

        def to_representation(self, obj):
            # for read functionality
            if obj.created_by != self.context['request'].user:
                return None
            else:
                return getattr(obj,field_name)
    return PrivateField

class QuizSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    def save(self, *args, **kwargs):
        validated_data = self.validated_data
        video_tutorial = validated_data["video_tutorial"]
        if video_tutorial.created_by  != self.context["request"].user:
            raise InvalidPermissionsException(detail="Invalid Permissions")
        return super().save(**kwargs)

    class Meta(AbstractModelSerializerMeta):
        model = Quiz
        fields = "__all__"

class VideoTutorialSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    quiz = QuizSerializer(read_only=True)
    def simple_validate_youtube_embed(self,url):
        from urllib import parse as urlparse
        import requests
        import re
        parsed_url = urlparse.urlparse(url)
        youtube_url_netlocs = ["youtube.com","youtu.be"]
        is_youtube_url = False
        for i in youtube_url_netlocs:
            if i in parsed_url.netloc:
                is_youtube_url = True
                break
        if not is_youtube_url:
            raise SimpleValidationError(detail='Provided link is not a valid youtube link')
        if "/embed" in parsed_url.path:
            return url 
        if parsed_url.path =="/watch" and parsed_url.query.startswith("v="):
            return "https://youtube.com/embed/"+parsed_url.query[2:]
        # hopefully it doesnt get here
        api_url = 'https://www.youtube.com/oembed'
        r = requests.get(api_url, params={"url":url})
        if r.status_code != 200:
            raise SimpleValidationError(detail='Unable to process link, check that video exists')
        results = r.json()
        m = re.search('''(<iframe[^>]+src=")([^"]*)(".*)''', result["html"])
        if not m:
            raise SimpleValidationError(detail='Unable to process link, check that video exists')
        return m.groups()[1]
        

    def validate(self, data):
        url = data.get("video_link",None)
        if url:
            val = URLValidator()
            try:
                val(url)
            except ValidationError:
                raise SimpleValidationError(detail="Invalid Url")
            embed_type = data['embed_type']
            valid_embed_types = [i[0] for i in VideoTutorial.EMBED_TYPES]
            if embed_type not in valid_embed_types:
                raise SimpleValidationError(detail='Invalid Embed Type')
            if embed_type==VideoTutorial.YOUTUBE_EMBED:
                data["video_link"]=self.simple_validate_youtube_embed(url)
        return data

    def create(self, validated_data):
        # for some reason i have to do this manually
        if self.context["request"].user:
            validated_data["created_by"]=self.context["request"].user
        validated_data["is_active"]=True
        instance = VideoTutorial.objects.create(**validated_data)
        return instance


    class Meta(AbstractModelSerializerMeta):
        model = VideoTutorial
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
                    raise SimpleValidationError(detail="Unique together constraint quiz_position violated")
                return data
        question = Question.objects.filter(quiz_id=quiz, position=position)
        if question:
            raise SimpleValidationError(detail="Unique together constraint quiz_position violated")
        return data

    def save(self,**kwargs):
        validated_data =  self.validated_data
        instance =  self.instance
        if instance:
            quiz =  instance.quiz
        else:
            quiz = validated_data["quiz"]
        if quiz.created_by != self.context["request"].user:
            raise InvalidPermissionsException(detail="Invalid Permissions")
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
            raise SimpleValidationError(detail="Unique together constraint quiz_position violated")
        return data

    class Meta(AbstractModelSerializerMeta):
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
                raise SimpleValidationError(detail="Unique together constraint question_position violated")
        return data

    def save(self, **kwargs):
        validated_data = self.validated_data
        instance =  self.instance
        if instance:
            question = self.instance.question
        else:
            question = validated_data["question"]
        if question.created_by != self.context["request"].user:
            raise InvalidPermissionsException(detail="Invalid Permisssions")
        return super().save(**kwargs)

            
    class Meta(AbstractModelSerializerMeta):
        model = MultiChoiceQuestionChoice
        fields = "__all__"

class MultiChoiceQuestionSerializer(AbstractSerializersMixin, QuestionsSerializerMixin, serializers.ModelSerializer):

    choices = MultiChoiceQuestionChoiceSerializer(many=True, read_only=True)
    question_type = serializers.CharField(read_only=True,)

    @transaction.atomic
    def create(self,validated_data):
        validated_data["question_type"] = Question.MULTI_CHOICE_QUESTION_TYPE
        return super().create(validated_data)

    class Meta(AbstractModelSerializerMeta):
        model = MultiChoiceQuestion
        fields = "__all__"

class FreeFormQuestionSerializer(AbstractSerializersMixin, QuestionsSerializerMixin, serializers.ModelSerializer):
    question_type = serializers.CharField(read_only=True,)
    answer = create_private_field(serializers.CharField,"answer")()

    @transaction.atomic
    def create(self,validated_data):
        validated_data["question_type"] = Question.FREE_FORM_QUESTION_TYPE
        return super().create(validated_data)

    class Meta(AbstractModelSerializerMeta):
        model = FreeFormQuestion
        fields = "__all__"

class QuizSolutionSerializer(AbstractSerializersMixin, serializers.ModelSerializer):

    start = serializers.ReadOnlyField()
    user = serializers.ReadOnlyField(source='user.id')
    time_taken = serializers.SerializerMethodField()

    def get_time_taken(self, obj):
        if not obj.complete:
            return None
        return strfdelta(obj.stop.replace(tzinfo=pytz.UTC) - obj.start.replace(tzinfo=pytz.UTC))
    def validate(self, data):
        if "quiz" in data.keys():
            _s=QuizSolution.objects.filter(quiz=data["quiz"], created_by=self.context["request"].user)
            if _s:
                if self.instance and self.instance == _s[0]:
                    pass
                else:
                    raise SimpleValidationError(detail="Solution for that quiz already exists")
        return data

    @transaction.atomic
    def create(self,validated_data):
        validated_data["start"]=datetime.datetime.utcnow()
        validated_data["user"]=self.context["request"].user
        return super().create(validated_data)

    class Meta(AbstractModelSerializerMeta):
        model = QuizSolution
        fields = AbstractModelSerializerMeta.DEFAULT_FIELDS + ["start","stop","retake","complete","total_points","user","time_taken","quiz"]
        read_ony_fields = AbstractModelSerializerMeta.read_ony_fields+["start","stop","retake","complete","total_points","user","time_taken","quiz"]
 

class AbstractSubmittedAnswerMixin:
    

    def validate(self, data):
        if self.partial and "question" not in data.keys():
            pass
        else:
            answer = self.Meta.model.objects.filter(created_by=self.context["request"].user, question=data["question"])
            if answer:
                if self.instance == answer:
                    pass
                else:
                    raise SimpleValidationError(detail="Question already has an answer")
        return data

    def create(self, validated_data):
        quiz = validated_data["question"].quiz
        try: 
            solution = QuizSolution.objects.get(quiz=quiz, user=self.context["request"].user)
            validated_data["solution"]=solution
            return super().create(validated_data)
        except QuizSolution.DoesNotExist:
            raise NotFound(detail="Quiz does not have a solution")

class SubmittedMultichoiceAnswerSerializer(AbstractSerializersMixin, AbstractSubmittedAnswerMixin, serializers.ModelSerializer):
    solution = serializers.ReadOnlyField(source="solution.id")
    class Meta(AbstractModelSerializerMeta):
        model = SubmittedMultichoiceAnswer
        fields = "__all__"
        read_ony_fields = AbstractModelSerializerMeta.read_ony_fields + ["solution"]

class SubmittedFreeformAnswerSerializer(AbstractSerializersMixin, AbstractSubmittedAnswerMixin, serializers.ModelSerializer):
    solution = serializers.ReadOnlyField(source="solution.id")
    class Meta(AbstractModelSerializerMeta):
        model = SubmittedFreeformAnswer
        fields = "__all__"
        read_ony_fields = AbstractModelSerializerMeta.read_ony_fields + ["solution"]


class SubmitQuizSerializer(serializers.Serializer):
    answer = serializers.CharField(max_length=255)
    question = serializers.IntegerField()
    solution =serializers.IntegerField()

    def validate(self, data):
        question = data["question"]
        solution = QuizSolution.objects.get(id=data["solution"])
        try:
            question:Question = Question.objects.get(id=question)
        except Question.DoesNotExist:
            raise NotFound(detail="Question with that id does not exist")
        model_mapper = {Question.FREE_FORM_QUESTION_TYPE:SubmittedFreeformAnswer,Question.MULTI_CHOICE_QUESTION_TYPE:SubmittedMultichoiceAnswer}
        if model_mapper[question.question_type].objects.filter(solution=solution,question_id=question.id):
            raise SimpleValidationError(detail="Question {_id} already has an answer".format(_id=question.id))
        return data
