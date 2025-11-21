from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'courses'

urlpatterns = [
    # Основные маршруты
    path('', views.home, name='home'),
    path('base/', views.base, name='base'),
    path('courses/', views.course_list, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/test/', views.lesson_test, name='lesson_test'),
    path('lesson/<int:lesson_id>/test/submit/', views.submit_test, name='submit_test'),
    path('lesson/<int:lesson_id>/test_result/', views.test_result_view, name='test_result'),
    path('accounts/logout/', views.custom_logout, name='logout'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('search/', views.search_courses, name='search'),
    path('application/', views.course_application, name='course_application'),
    path('application/<int:course_id>/', views.course_application, name='course_application_with_course'),
    # Личный кабинет
    path('profile/', views.profile, name='profile'),
    path('course-progress/<int:course_id>/', views.course_progress_detail, name='course_progress_detail'),
    # Админка заявок
    path('applications/', views.applications_dashboard, name='applications_dashboard'),
    path('applications/<int:application_id>/update/', views.update_application_status, name='update_application_status'),
    path('logout-confirm/', views.logout_confirm, name='logout_confirm'),
]