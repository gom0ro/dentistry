from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Course, Lesson, Question, UserCourseAccess, UserProgress, TestResult, CourseApplication,Answer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    min_num = 4  # Минимум 4 ответа (1 правильный, 3 неправильных)

# Базовые админ-классы без сложных полей
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    search_fields = ['title', 'description']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course']
    list_filter = ['course']
    search_fields = ['title', 'content']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'lesson', 'get_correct_answer']
    list_filter = ['lesson']
    inlines = [AnswerInline]
    
    def get_correct_answer(self, obj):
        correct = obj.answers.filter(is_correct=True).first()
        return correct.text if correct else "No correct answer"
    get_correct_answer.short_description = 'Correct Answer'

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct']
    list_filter = ['question__lesson', 'is_correct']



@admin.register(UserCourseAccess)
class UserCourseAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'purchased_at']
    list_filter = ['course']
    search_fields = ['user__username', 'course__title']

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson']
    list_filter = ['lesson__course']
    search_fields = ['user__username', 'lesson__title']

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'score', 'total_questions']
    list_filter = ['lesson__course']
    search_fields = ['user__username', 'lesson__title']

@admin.register(CourseApplication)
class CourseApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'course', 'status', 'created_at']
    list_filter = ['status', 'course']
    search_fields = ['name', 'phone', 'email', 'course__title']

# Настройки админки
admin.site.site_header = "ComfortDentall - Администрирование"
admin.site.site_title = "ComfortDentall Admin"
admin.site.index_title = "Панель управления"