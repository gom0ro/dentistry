from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import re
from django.db.models.signals import post_save
from django.dispatch import receiver

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='course_images/')
    duration = models.CharField(max_length=100, help_text="Например: 2 месяца")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0, help_text="Порядок урока внутри курса")
    video_url = models.URLField(help_text="Ссылка на YouTube видео", blank=True)
    duration = models.CharField(max_length=50, blank=True, help_text="Например: 15 минут")
    description = models.TextField(blank=True)

    # Конспект урока (HTML разрешён)
    text_content = models.TextField(
        blank=True,
        null=True,
        help_text="Конспект урока: можно вставлять HTML"
    )

    class Meta:
        ordering = ['order']
        unique_together = (('course', 'order'),)  # не обязательно, но полезно

    def __str__(self):
        return f"{self.course.title} — {self.title}"

    def get_youtube_id(self):
        """
        Возвращает id видео из youtube url или None.
        Поддерживает форматы:
        - https://www.youtube.com/watch?v=VIDEOID
        - https://youtu.be/VIDEOID
        - с параметрами &...
        """
        if not self.video_url:
            return None
        # Ищем id между v= и & или после youtu.be/
        match = re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_-]{6,})', self.video_url)
        if match:
            return match.group(1)
        return None

    @property
    def get_next_lesson(self):
        return Lesson.objects.filter(course=self.course, order__gt=self.order).order_by('order').first()


class LessonOutcome(models.Model):
    lesson = models.ForeignKey(Lesson, related_name='outcomes', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.lesson.title} — {self.text}"
class Question(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()

    def __str__(self):
        return self.text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class UserCourseAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user', 'lesson']

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"

class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percentage = models.FloatField(default=0)         
    passed = models.BooleanField(default=False)       
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'lesson']

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({self.score}/{self.total_questions})"

    def get_percentage(self):
        """Возвращает процент правильных ответов"""
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100)

    def score_class(self):
        """Возвращает CSS класс для отображения результата"""
        percentage = self.get_percentage()
        if percentage >= 90:
            return "excellent"
        elif percentage >= 70:
            return "good"
        elif percentage >= 50:
            return "average"
        else:
            return "poor"


class CourseApplication(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('processed', 'В обработке'),
        ('completed', 'Завершена'),
        ('rejected', 'Отклонена'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Имя')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, verbose_name='Курс')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    notes = models.TextField(blank=True, verbose_name='Заметки')
    
    user = models.ForeignKey(
    User, 
    on_delete=models.CASCADE, 
    null=True, 
    blank=True,
    verbose_name='Пользователь'
)
    
    class Meta:
        verbose_name = 'Заявка на курс'
        verbose_name_plural = 'Заявки на курсы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.course.title}"
    
class UserProfile(models.Model):
    SPECIALIZATION_CHOICES = [
        ('orthodontics', 'Ортодонтия'),
        ('therapy', 'Терапевтическая стоматология'),
        ('surgery', 'Хирургическая стоматология'),
        ('implantology', 'Имплантология'),
        ('periodontology', 'Пародонтология'),
        ('pediatric', 'Детская стоматология'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(
        max_length=50, 
        choices=SPECIALIZATION_CHOICES, 
        default='orthodontics'
    )
    bio = models.TextField(max_length=500, blank=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    related_name='profile'
)
    
    def __str__(self):
        return f"{self.user.username} Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()