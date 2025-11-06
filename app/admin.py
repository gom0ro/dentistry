from django.contrib import admin
from .models import Course, Lesson, Question, Answer, UserCourseAccess, UserProgress, TestResult

# ----------------------
# Встроенные ответы для вопросов
# ----------------------
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    verbose_name = "Ответ"
    verbose_name_plural = "Ответы"

# ----------------------
# Вопросы
# ----------------------
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]
    list_display = ['text', 'course_title']
    
    def course_title(self, obj):
        return obj.lesson.course.title
    course_title.short_description = "Курс"

# ----------------------
# Встроенные уроки для курса
# ----------------------
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    verbose_name = "Урок"
    verbose_name_plural = "Уроки"

# ----------------------
# Курсы
# ----------------------
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ['title', 'price', 'is_active', 'created_at']
    list_display_links = ['title']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title']
    verbose_name = "Курс"
    verbose_name_plural = "Курсы"

# ----------------------
# Доступ пользователей к курсу
# ----------------------
class UserCourseAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'purchased_at', 'is_active']
    list_filter = ['is_active', 'purchased_at']
    search_fields = ['user__username', 'course__title']
    verbose_name = "Доступ пользователя к курсу"
    verbose_name_plural = "Доступы пользователей к курсам"

# ----------------------
# Прогресс пользователей
# ----------------------
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'is_completed', 'completed_at']
    list_filter = ['is_completed', 'completed_at']
    verbose_name = "Прогресс пользователя"
    verbose_name_plural = "Прогресс пользователей"

# ----------------------
# Результаты тестов
# ----------------------
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'score', 'total_questions', 'get_percentage', 'completed_at']
    list_filter = ['completed_at']
    verbose_name = "Результат теста"
    verbose_name_plural = "Результаты тестов"

# ----------------------
# Регистрация моделей в админке
# ----------------------
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson)
admin.site.register(Question, QuestionAdmin)
admin.site.register(UserCourseAccess, UserCourseAccessAdmin)
admin.site.register(UserProgress, UserProgressAdmin)
admin.site.register(TestResult, TestResultAdmin)
