import abc, json, datetime
from django.conf import settings
from eneza.models import SubmittedMultichoiceAnswer, SubmittedFreeformAnswer,\
    MultiChoiceQuestion,QuizSolution, MultiChoiceQuestionChoice, FreeFormQuestion, QuizSolutionActivity
from eneza.exceptions import SimpleValidationError
from eneza.services.mailer import Mailer
from .utils import strfdelta
import pytz

class AbstractQuizService(abc.ABC):

    @abc.abstractproperty
    def errors(self):
        pass

    @abc.abstractmethod
    def validate_multichoice_answer(self, answer:SubmittedMultichoiceAnswer):
        pass

    @abc.abstractmethod
    def validate_freeform_answer(self, answer:SubmittedFreeformAnswer):
        pass


class QuizService(AbstractQuizService):

    def __init__(self, *args, **kwargs):
        self._errors={}
        self.mailer = Mailer()

    @property
    def errors(self):
        return self._errors

    def validate_multichoice_answer(self,answer:SubmittedMultichoiceAnswer):
        question:MultiChoiceQuestion = answer.question
        choice:MultiChoiceQuestionChoice = MultiChoiceQuestionChoice.objects.filter(answer=True,question=question)
        if choice:
            if answer.selected_choice == choice[0]:
                return True
        return False

    def validate_freeform_answer(self, answer:SubmittedFreeformAnswer):
        question:FreeFormQuestion = answer.question
        # @todo change answer field to array to allow multiple answer variants
        return answer.answer.lower() == question.answer.lower()

    def process_solution(self, solution:QuizSolution, stop=True):
        # if solution.complete:
        #     raise SimpleValidationError(detail="Solution already submitted")
        points = 0
        mutichoice_answers = SubmittedMultichoiceAnswer.objects.filter(solution_id=solution.id)
        freeform_answers = SubmittedFreeformAnswer.objects.filter(solution_id=solution.id)
        for answer in freeform_answers:
            if self.validate_freeform_answer(answer):
                answer.is_valid=True
                answer.save()
                points += answer.question.points
        for answer in mutichoice_answers:
            if self.validate_multichoice_answer(answer):
                answer.is_valid=True
                answer.save()
                points += answer.question.points
        solution.total_points= points
        solution.complete=True
        if stop:
            stop = datetime.datetime.utcnow()
            solution.stop = stop
            solution.save()
            context = {"time":stop.isoformat(),"points":points}
            end_activity = QuizSolutionActivity(solution=solution,
                    activity=QuizSolutionActivity.END_TEST, context=json.dumps(context)
                )
            end_activity.save()
        solution.save()
        return solution

    def send_quiz_results_email(self, solution:QuizSolution):
        template = 'emails/quiz_results.html'
        user = solution.created_by
        time_taken = solution.stop.replace(tzinfo=pytz.UTC) - solution.start.replace(tzinfo=pytz.UTC)
        context = {"quiz":solution.quiz, "solution":solution, "user":user, "time_taken":strfdelta(time_taken)}
        mailer = Mailer()
        mailer.send_email("Quiz Results",settings.DEFAULT_FROM_EMAIL,[user.email],template,context)
        solution.sent_notification =True
        solution.save()



        
