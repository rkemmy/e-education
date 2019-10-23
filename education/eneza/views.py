from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FileUploadParser,MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend

from education.eneza.serializers import VideoTutorialSerializer, QuizSerializer,\
    MultiChoiceQuestionSerializer, QuestionSerializer, FreeFormQuestionSerializer, MultiChoiceQuestionChoiceSerializer,\
    SubmittedSolutionSerializer, SubmittedMultichoiceAnswerSerializer, SubmittedFreeformAnswerSerializer,SubmittedAnswerSerializer

from education.eneza.models import VideoTutorial, Quiz, MultiChoiceQuestion,\
    Question, FreeFormQuestion, MultiChoiceQuestionChoice, SubmittedSolution,\
    SubmittedAnswer, SubmittedFreeformAnswer, SubmittedMultichoiceAnswer


class VideoTutorialView(ModelViewSet):
    parser_classes = (MultiPartParser,FormParser,)
    permission_classes = (IsAuthenticated,)
    serializer_class = VideoTutorialSerializer
    queryset =  VideoTutorial.objects.all()

class QuizView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = QuizSerializer
    queryset = Quiz.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['video_tutorial',]


class QuestionView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = QuestionSerializer
    queryset = Question.objects.all().prefetch_related()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['quiz','position']

    def _serialize(self, request, instance):
        children_models=[
            (FreeFormQuestion,"freeformquestion", FreeFormQuestionSerializer),
            (MultiChoiceQuestion,"multichoicequestion",MultiChoiceQuestionSerializer),
            ]
        for model, related_query_name, s in children_models:
            try:
                i=getattr(instance,related_query_name)
                return s(instance=i, context={'request':request}).data
            except model.DoesNotExist:
                continue
        return self.serializer_class(instance=instance).data

    def serialize_questions(self,request, queryset, many=True):
        data = [] if many==True else {}
        if many==True:
            for q in queryset:
                data.append(self._serialize(request, q))
            return data
        else:
            return self._serialize(request, queryset)

    def list(self, request):
        queryset=self.filter_queryset(self.get_queryset())
        data =self.serialize_questions(request, queryset)
        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        try:
            question=Question.objects.get(id=pk)
            data =self.serialize_questions(request, question, many=False)
            return Response(data, status=status.HTTP_200_OK)
        except Question.DoesNotExist:
            return Response({"error":"Question with that Id does not exists"}, status=status.HTTP_404_NOT_FOUND)

class MultiChoiceQuestionView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = MultiChoiceQuestionSerializer
    queryset = MultiChoiceQuestion.objects.all()

    def partial_update(self, request, pk=None):
        try:
            _mquestion=MultiChoiceQuestion.objects.get(pk=pk)
            serializer = MultiChoiceQuestionSerializer(_mquestion, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MultiChoiceQuestion.DoesNotExist:
            return Response({"error":"Question with that Id does not exists"}, status=status.HTTP_404_NOT_FOUND)

class MultiChoiceQuestionChoiceView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = MultiChoiceQuestionChoiceSerializer
    queryset = MultiChoiceQuestionChoice.objects.all()
    filter_backends =[ DjangoFilterBackend]
    filterset_fields = ["question"]

class FreeFormQuestionView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = FreeFormQuestionSerializer
    queryset = FreeFormQuestion.objects.all()


class SubmittedSoutionView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubmittedSolutionSerializer
    queryset = SubmittedSolution.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["quiz","user"]

class SubmittedAnswerView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubmittedAnswerSerializer
    queryset = SubmittedAnswer.objects.all().prefetch_related()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['solution','question']

    def _serialize(self, request, instance):
        children_models=[
            (SubmittedFreeformAnswer,"submittedfreeformanswer", SubmittedFreeformAnswerSerializer),
            (SubmittedMultichoiceAnswer,"submittedmultichoiceanswer",SubmittedMultichoiceAnswerSerializer),
            ]
        for model, related_query_name, s in children_models:
            try:
                i=getattr(instance,related_query_name)
                return s(instance=i, context={'request':request}).data
            except model.DoesNotExist:
                continue
        return self.serializer_class(instance=instance).data

    def serialize_answers(self,request, queryset, many=True):
        data = [] if many==True else {}
        if many==True:
            for q in queryset:
                data.append(self._serialize(request, q))
            return data
        else:
            return self._serialize(request, queryset)

    def list(self, request):
        queryset=self.filter_queryset(self.get_queryset())
        data =self.serialize_answers(request, queryset)
        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        try:
            question=Question.objects.get(id=pk)
            data =self.serialize_answers(request, question, many=False)
            return Response(data, status=status.HTTP_200_OK)
        except Question.DoesNotExist:
            return Response({"error":"Question with that Id does not exists"}, status=status.HTTP_404_NOT_FOUND)


class SubmittedFreeformAnswerView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubmittedFreeformAnswerSerializer
    queryset = SubmittedFreeformAnswer.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["solution","question"]

class SubmittedMultichoiceAnswerView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubmittedMultichoiceAnswerSerializer
    queryset = SubmittedMultichoiceAnswer.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["solution","question"]
