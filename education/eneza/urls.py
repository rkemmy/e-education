from django.urls import path, include
from rest_framework import routers
from education.eneza.views import VideoTutorialView, QuizView, MultiChoiceQuestionView,\
    QuestionView, MultiChoiceQuestionChoiceView, FreeFormQuestionView,SubmittedAnswerView,\
    SubmittedMultichoiceAnswerView, SubmittedFreeformAnswerView, SubmittedSoutionView

router = routers.DefaultRouter()
router.register(r'video_tutorials', VideoTutorialView, base_name='video-tutorials-view')
router.register(r'quiz', QuizView, base_name='quiz-view')
router.register(r'questions', QuestionView, base_name='question-view')
router.register(r'multi-choice-questions', MultiChoiceQuestionView, base_name='multi-choice-question-view')
router.register(r'free-form-questions', FreeFormQuestionView, base_name='free-form-question-view')
router.register(r'multi-choices', MultiChoiceQuestionChoiceView, base_name='multi-choice-view')
router.register(r'submitted-solutions', SubmittedSoutionView, base_name='submitted-solutions-view')
router.register(r'submitted-answers', SubmittedAnswerView, base_name='submitted-answers-view')
router.register(r'submitted-multichoice-answers', SubmittedMultichoiceAnswerView, base_name='submitted-multichoice-answers-view')
router.register(r'submitted-freeform-answers', SubmittedFreeformAnswerView, base_name='submitted-freeform-answers-view')

urlpatterns = [
    path("", include(router.urls)),
]

