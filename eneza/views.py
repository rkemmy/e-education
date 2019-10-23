from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FileUploadParser,MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound
from django_filters.rest_framework import DjangoFilterBackend

from eneza.serializers import VideoTutorialSerializer, QuizSerializer,\
    MultiChoiceQuestionSerializer, QuestionSerializer, FreeFormQuestionSerializer, MultiChoiceQuestionChoiceSerializer,\
    QuizSolutionSerializer, SubmittedMultichoiceAnswerSerializer, SubmittedFreeformAnswerSerializer, SubmitQuizSerializer

from eneza.models import VideoTutorial, Quiz, MultiChoiceQuestion,\
    Question, FreeFormQuestion, MultiChoiceQuestionChoice, QuizSolution,\
    SubmittedFreeformAnswer, SubmittedMultichoiceAnswer

from eneza.exceptions import InvalidPermissionsException,SimpleValidationError
from eneza.services.quiz_service import QuizService


class ExtendedModelViewSet(ModelViewSet):

    def creator_filter(self, queryset,user):
        return queryset.filter(created_by=user)

    def is_creator(self, obj,user, raise_exception=True):
        status = obj.created_by==user
        if status==False:
            if raise_exception:
                raise InvalidPermissionsException(detail="You do not have permission to read this object")
        return status

    def get_obj_or_404(self, Model, pk, raise_exception=True, detail="object with that id does not exists"):
        try:
            return Model.objects.get(pk=pk)
        except Model.DoesNotExist:
            if raise_exception:
                raise NotFound(detail=detail)
            return False

ModelViewSet=ExtendedModelViewSet

class VideoView(ModelViewSet):
    parser_classes = (MultiPartParser,FormParser,)
    permission_classes = (IsAuthenticated,)
    serializer_class = VideoTutorialSerializer
    queryset =  VideoTutorial.objects.all()   


class VideoTutorialView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = VideoTutorialSerializer
    queryset =  VideoTutorial.objects.all() 

class CustomQuestionSerializer:
    parent_serializer_class = QuestionSerializer

    def __init__(self, request, queryset=None, many=True, with_answer=False):
        self.request = request
        self.queryset = queryset
        self.many = many
        self._data = []
        self.with_answer = with_answer

    @property
    def data(self):
        return self.serialize_questions(self.queryset, many=self.many)

    def _serialize(self, instance):
        children_models=[
            (FreeFormQuestion,"freeformquestion", FreeFormQuestionSerializer, (SubmittedFreeformAnswer, SubmittedFreeformAnswerSerializer)),
            (MultiChoiceQuestion,"multichoicequestion",MultiChoiceQuestionSerializer, (SubmittedMultichoiceAnswer, SubmittedMultichoiceAnswerSerializer)),
            ]
        for model, related_query_name, s,_a_s in children_models:
            try:
                i=getattr(instance,related_query_name)
                data = s(instance=i, context={'request':self.request}).data
                if self.with_answer:
                    try:
                        answer = _a_s[0].objects.get(question=i, created_by=self.request.user)
                        answer = _a_s[1](instance=answer,  context={'request':self.request}).data
                    except _a_s[0].DoesNotExist:
                        answer = None
                    data["user_answer"]=answer
                return data
            except model.DoesNotExist:
                continue
        return self.parent_serializer_class(instance=instance, context={'request':self.request}).data 

    def serialize_questions(self, queryset, many=True):
        data = [] if many==True else {}
        if many==True:
            for q in self.queryset:
                data.append(self._serialize(q))
            return data
        else:
            return self._serialize(queryset)  

class QuizView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = QuizSerializer
    queryset = Quiz.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['video_tutorial',]
    quiz_service = QuizService

    def get_user_quiz_solution(self,quiz, user, raise_exception=True):
        try: 
            solution = QuizSolution.objects.get(quiz=quiz, user=user)
            return solution
        except QuizSolution.DoesNotExist:
            if raise_exception:
                raise NotFound(detail="Quiz does not have a solution")
            return False

    @action(detail=True, methods=["GET"])
    def start_quiz(self, request, pk=None):
        quiz = self.get_obj_or_404(Quiz,pk)
        solution = self.get_user_quiz_solution(quiz, request.user, raise_exception=False)
        if solution != False:
            raise SimpleValidationError(detail="User already started quiz")
        serializer = QuizSolutionSerializer(data={"quiz":quiz.id}, context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def _end_quiz(self, request, quiz):
        solution:QuizSolution = self.get_user_quiz_solution(quiz, request.user, raise_exception=True)
        if solution.complete:
            return SimpleValidationError(detail="Quiz solution has already been submitted")

        self.is_creator(solution, request.user, raise_exception=True)
        quiz_service = self.quiz_service()
        _solution = quiz_service.process_solution(solution)
        try:
            quiz_service.send_quiz_results_email(_solution)
        except Exception as e:
            print(e)
            pass
        if _solution and isinstance(_solution, QuizSolution):
            serializer = QuizSolutionSerializer(instance=_solution,many=False,context={"request":request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(quiz_service.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True,methods=["GET"])
    def end_quiz(self, request, pk=None):
        quiz = self.get_obj_or_404(Quiz,pk)
        return self._end_quiz(request,quiz)
    
    @action(detail=True, methods=["GET"])
    def quiz_solution(self, request, pk=None):
        quiz = self.get_obj_or_404(Quiz, pk)
        solution = self.get_user_quiz_solution(quiz, request.user, raise_exception=True)
        self.is_creator(solution, request.user, raise_exception=True)
        serializer = QuizSolutionSerializer(instance=solution, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["GET"])
    def quiz_questions(self, request, pk=None):
        quiz = self.get_obj_or_404(Quiz, pk)
        solution = self.get_user_quiz_solution(quiz, request.user, raise_exception=False)
        if solution == False and quiz.created_by !=request.user:
            raise SimpleValidationError(detail="Must start quiz or be quiz owner to view questions")
        position = request.GET.get('position', None)
        if position:
            try:
                position=int(position)
            except Exception:
                raise SimpleValidationError(detail='position must be an integer')
            try:
                question = Question.objects.get(quiz=quiz, position=int(position))
                serializer = CustomQuestionSerializer(request, queryset=question, many=False, with_answer=True)

            except Question.DoesNotExist:
                raise NotFound(detail="Question does not exist")
        else:
            questions =  Question.objects.filter(quiz=quiz).order_by('position')
            serializer = CustomQuestionSerializer(request, queryset=questions, many=True, with_answer=True)
        data =serializer.data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"])
    def submit_quiz(self, request, pk=None):
        if type(request.data) != list:
            raise SimpleValidationError(detail="Bad Request")
        quiz = self.get_obj_or_404(Quiz, pk)
        solution:QuizSolution = self.get_user_quiz_solution(quiz, request.user, raise_exception=True)
        if solution.complete:
            raise SimpleValidationError(detail="Already submitted solution for quiz")

        validated_data=[]
        
        for d in request.data:
            d["solution"]=solution.id

            s= SubmitQuizSerializer(data=d, context={"request":request})
            if s.is_valid(raise_exception=True):
                validated_data.append(s.data)
        free_form_answers=[]
        multi_choice_answers=[]
        models_mapper = {Question.FREE_FORM_QUESTION_TYPE:SubmittedFreeformAnswer,
                    Question.MULTI_CHOICE_QUESTION_TYPE:SubmittedMultichoiceAnswer}
        for d in validated_data:
            question:Question = Question.objects.get(id=d["question"])
            _M =  models_mapper[question.question_type]
            if  _M.objects.filter(question_id=question.id, created_by=request.user):
                raise SimpleValidationError(detail="Question {_id} already has an answer".format(_id=question.id))

            if question.question_type==Question.MULTI_CHOICE_QUESTION_TYPE:
                question:MultiChoiceQuestion = question.multichoicequestion
                try:
                    choice = int(d["answer"])
                except Exception:
                    raise SimpleValidationError(detail="Choice must be an integer")
                choice = self.get_obj_or_404(MultiChoiceQuestionChoice, choice, detail="Choice does not exist")
                multi_choice_answers.append(
                    _M(selected_choice=choice,solution=solution,question=question)
                )
            if  question.question_type==Question.FREE_FORM_QUESTION_TYPE:
                question:FreeFormQuestion = question.freeformquestion 
                free_form_answers.append(
                    _M(solution=solution, question=question, answer=d["answer"])
                )
        _x = [(free_form_answers,SubmittedFreeformAnswer),(multi_choice_answers,SubmittedMultichoiceAnswer)]
        for instances, _M in _x:
            try:
                _M.objects.bulk_create(instances)
            except Exception as e:
                raise SimpleValidationError(detail="Unable to create answers"+str(e))
        return self._end_quiz(request, quiz)
        

    def destroy(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)   


class QuestionView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = QuestionSerializer
    queryset = Question.objects.all().order_by('position')
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

    def create(self, request):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

    def update(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

    def partial_update(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)   

    def list(self, request):
        queryset=self.filter_queryset(self.get_queryset())
        data =self.serialize_questions(request, queryset)
        # data = self.serializer_class(instance=queryset, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        question = self.get_obj_or_404(Question, pk)
        data =self.serialize_questions(request, question, many=False)
        return Response(data, status=status.HTTP_200_OK)

 
class MultiChoiceQuestionView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = MultiChoiceQuestionSerializer
    queryset = MultiChoiceQuestion.objects.all()


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
    filter_backends =[ DjangoFilterBackend]
    filterset_fields = ["question"]


class SubmittedFreeformAnswerView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubmittedFreeformAnswerSerializer
    queryset = SubmittedFreeformAnswer.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["solution","question"]

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={"request":request})
        print(serializer.Meta.read_ony_fields)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

class SubmittedMultichoiceAnswerView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubmittedMultichoiceAnswerSerializer
    queryset = SubmittedMultichoiceAnswer.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["solution","question"]

    def destroy(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)