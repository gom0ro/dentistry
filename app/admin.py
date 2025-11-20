from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Course, Lesson, Question, UserCourseAccess, UserProgress, TestResult, CourseApplication

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
    list_display = ['text', 'lesson']
    list_filter = ['lesson__course']
    search_fields = ['text']

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