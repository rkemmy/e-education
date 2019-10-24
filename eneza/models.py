from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.utils.translation import gettext_lazy


class AbstractBaseManager(models.Manager):
    use_in_migrations = True
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class AbstractModel(models.Model):
    is_active = models.BooleanField(default=True)
    created_at =  models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)ss_creator",
        related_query_name="%(app_label)s_%(class)ss_updater",
        blank=True, null=True
    )
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)ss_updated_by",
        related_query_name="%(app_label)s_%(class)ss_updated_by",
        blank=True, null=True
    )

    items = models.Manager()
    objects = AbstractBaseManager()

    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

    class Meta:
        abstract = True
        ordering = ('-updated_at', '-created_at')


class Instructor(AbstractModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='instructor', on_delete=models.CASCADE)

    class Meta:
        db_table = 'instructors'
        verbose_name_plural = gettext_lazy('Instructors')


class Student(AbstractModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='student', on_delete=models.CASCADE)

    class Meta:
        db_table = 'students'
        verbose_name_plural = gettext_lazy('Students')


class Video(AbstractModel):
    MAX_VIDEO_UPLOAD_SIZE = settings.MAX_VIDEO_UPLOAD_SIZE
    ALLOWED_VIDEO_EXTENSIONS = settings.ALLOWED_VIDEO_EXTENSIONS
    video = models.FileField(validators=[FileExtensionValidator(ALLOWED_VIDEO_EXTENSIONS)], upload_to='video_tutorials')
    class Meta:
        verbose_name_plural = gettext_lazy('Videos')
        db_table = 'videos'


class VideoTutorial(AbstractModel):
    YOUTUBE_EMBED='Youtube'
    OTHER_EMBED='Other'
    EMBED_TYPES=(
        (YOUTUBE_EMBED,YOUTUBE_EMBED),
        (OTHER_EMBED, OTHER_EMBED)
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    video_link = models.TextField()
    embed_type = models.CharField(choices=EMBED_TYPES, max_length=255)

    class Meta:
        verbose_name_plural = gettext_lazy('VideoTutorials')
        db_table = 'video_tutorials'


class Quiz(AbstractModel):
    video_tutorial = models.OneToOneField('VideoTutorial', related_name='quiz', on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = gettext_lazy('Quizes')
        db_table = 'quizes'


class Question(AbstractModel):
    MULTI_CHOICE_QUESTION_TYPE='MULTI_CHOICE_QUESTION_TYPE'
    FREE_FORM_QUESTION_TYPE='FREE_FORM_QUESTION_TYPE'
    QUESTION_TYPE=(
        (MULTI_CHOICE_QUESTION_TYPE,MULTI_CHOICE_QUESTION_TYPE),
        (FREE_FORM_QUESTION_TYPE, FREE_FORM_QUESTION_TYPE)
    )
    quiz = models.ForeignKey('Quiz', related_name='questios', on_delete=models.CASCADE)
    question_type = models.CharField(max_length=100, choices=QUESTION_TYPE)
    position = models.PositiveIntegerField()
    content =  models.TextField()
    points = models.PositiveIntegerField(default=1)

    class Meta:
        db_table='questions'
        constraints = [
                models.UniqueConstraint(fields=['position', 'quiz_id'], name="quiz-question-position")
                ]
        verbose_name_plural = gettext_lazy('Questions')
        ordering = ('-position',)


class MultiChoiceQuestion(Question):
  
    class Meta(Question.Meta):
        db_table='multi_choice_questions'
        verbose_name_plural = 'MultiChoiceQuestions'


class MultiChoiceQuestionChoice(AbstractModel):
    question = models.ForeignKey('MultiChoiceQuestion', related_name='choices', on_delete=models.CASCADE)
    choice = models.TextField()
    position = models.PositiveIntegerField()
    answer = models.BooleanField(default=False)

    class Meta:
        db_table='multi_choice_question_choices'
        constraints = [
                models.UniqueConstraint(fields=['position', 'question_id'], name="question-position-choice")
                ]
        verbose_name_plural = gettext_lazy('MultiChoiceQuestionChoices')
        ordering = ('-position',)


class FreeFormQuestion(Question):
    answer = models.TextField()

    class Meta(Question.Meta):
        db_table='free_form_questions'
        verbose_name_plural = 'FreeFormQuestions'


class QuizSolution(AbstractModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user_submitted_solutions", on_delete=models.PROTECT)
    quiz = models.ForeignKey(Quiz, related_name="quiz_submitted_solutions", on_delete=models.PROTECT)
    start = models.DateTimeField()
    stop = models.DateTimeField(null=True)
    retake = models.BooleanField(default=False)
    complete = models.BooleanField(default=False)
    total_points = models.PositiveIntegerField(default=0)
    sent_notification = models.BooleanField(default=False)

    class Meta:
        db_table='quiz_solutions'
        constraints = [
                models.UniqueConstraint(fields=['user', 'quiz'], name="user-quiz")
                ]
        verbose_name_plural = gettext_lazy('QuizSolutions')


class QuizSolutionActivity(AbstractModel):
    RETAKE_COUNT="RETAKE_COUNT"
    START_TEST="START_TEST"
    END_TEST="END_TEST"
    CANCEL_TEST="CANCEL_TEST"
    ACTIVITIES =[
        (RETAKE_COUNT, RETAKE_COUNT),
        (START_TEST, START_TEST),
        (END_TEST, END_TEST),
        (CANCEL_TEST, CANCEL_TEST),
    ]
    solution = models.ForeignKey(QuizSolution, related_name='solution_activities', on_delete=models.PROTECT)
    activity = models.CharField(max_length=255, choices=ACTIVITIES)
    context = models.TextField()

    class Meta:
        db_table='quiz_solution_activities'
        verbose_name_plural = gettext_lazy('QuizSolutionActivies')


class SubmittedMultichoiceAnswer(AbstractModel):
    solution = models.ForeignKey(QuizSolution, related_name='quiz_multichoice_answers', on_delete=models.PROTECT)
    question = models.ForeignKey(MultiChoiceQuestion, related_name="multichoice_answers", on_delete=models.PROTECT)
    selected_choice = models.ForeignKey(MultiChoiceQuestionChoice, related_name="choice_answers", on_delete=models.PROTECT)
    is_valid = models.BooleanField(default=False)

    class Meta:
        db_table='submitted_multichoice_answers'
        constraints = [
                models.UniqueConstraint(fields=['solution', 'question'], name="multichoice_solution_question"),
                models.UniqueConstraint(fields=['question', 'created_by'], name="multichoice_question_creator"),
            ]
        verbose_name_plural = gettext_lazy('SubmittedMultichoiceAnswers')


class SubmittedFreeformAnswer(AbstractModel):
    solution = models.ForeignKey(QuizSolution, related_name='quiz_freeform_answers', on_delete=models.PROTECT)
    question = models.ForeignKey(FreeFormQuestion, related_name="freeform_answers", on_delete=models.PROTECT)
    answer = models.TextField()
    is_valid = models.BooleanField(default=False)

    class Meta:
        db_table='submitted_freeform_answers'
        constraints = [
                models.UniqueConstraint(fields=['solution', 'question'], name="freeform_solution_question"),
                models.UniqueConstraint(fields=['question', 'created_by'], name="freeform_question_creator"),
            ]
        verbose_name_plural = gettext_lazy('SubmittedFreeformAnswers')
