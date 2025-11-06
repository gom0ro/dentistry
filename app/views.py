from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout 
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Course, Lesson, TestResult, UserCourseAccess, UserProgress

def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                next_url = request.GET.get('next', '/profile/')
                return redirect(next_url)
        messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})

@login_required
def profile(request):
    # Получаем курсы пользователя
    user_courses = UserCourseAccess.objects.filter(user=request.user, is_active=True)
    
    # Прогресс по каждому курсу
    course_progress = []
    for access in user_courses:
        course = access.course
        total_lessons = course.lessons.count()
        completed_lessons = UserProgress.objects.filter(
            user=request.user, 
            lesson__course=course
        ).count()
        
        progress_percentage = 0
        if total_lessons > 0:
            progress_percentage = round((completed_lessons / total_lessons) * 100, 1)
        
        course_progress.append({
            'course': course,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': progress_percentage,
            'purchased_at': access.purchased_at
        })
    
    # Последние результаты тестов
    recent_results = TestResult.objects.filter(user=request.user).order_by('-completed_at')[:5]
    
    context = {
        'course_progress': course_progress,
        'recent_results': recent_results,
    }
    return render(request, 'courses/profile.html', context)

@login_required
def course_progress_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Проверяем доступ пользователя к курсу
    if not UserCourseAccess.objects.filter(user=request.user, course=course, is_active=True).exists():
        messages.error(request, 'У вас нет доступа к этому курсу.')
        return redirect('courses:profile')
    
    lessons = course.lessons.all()
    lesson_progress = []
    
    for lesson in lessons:
        progress = UserProgress.objects.filter(user=request.user, lesson=lesson).first()
        test_result = TestResult.objects.filter(user=request.user, lesson=lesson).first()
        
        lesson_progress.append({
            'lesson': lesson,
            'is_completed': progress.is_completed if progress else False,
            'test_result': test_result,
            'completed_at': progress.completed_at if progress else None
        })
    
    context = {
        'course': course,
        'lesson_progress': lesson_progress,
    }
    return render(request, 'courses/course_progress.html', context)

def course_list(request):
    courses = Course.objects.filter(is_active=True)
    user_has_access = []
    
    if request.user.is_authenticated:
        user_has_access = UserCourseAccess.objects.filter(
            user=request.user, 
            is_active=True
        ).values_list('course_id', flat=True)
    
    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'user_has_access': user_has_access
    })

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # Получаем уроки курса с правильным порядком
    lessons = course.lessons.all().order_by('order')
    
    # Проверяем доступ пользователя
    has_access = False
    if request.user.is_authenticated:
        has_access = UserCourseAccess.objects.filter(
            user=request.user, 
            course=course, 
            is_active=True
        ).exists()
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'lessons': lessons,  # Добавляем уроки в контекст
        'has_access': has_access
    })

@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Проверяем доступ к курсу
    has_access = UserCourseAccess.objects.filter(
        user=request.user, 
        course=lesson.course, 
        is_active=True
    ).exists()
    
    if not has_access:
        messages.error(request, 'У вас нет доступа к этому уроку.')
        return redirect('courses:course_detail', course_id=lesson.course.id)
    
    # Отмечаем урок как пройденный
    UserProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'is_completed': True}
    )
    
    return render(request, 'courses/lesson_detail.html', {'lesson': lesson})

@login_required
def submit_test(request, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        # Проверяем доступ к курсу
        has_access = UserCourseAccess.objects.filter(
            user=request.user, 
            course=lesson.course, 
            is_active=True
        ).exists()
        
        if not has_access:
            return JsonResponse({'success': False, 'error': 'Нет доступа'}, status=403)
        
        data = request.POST
        questions = lesson.questions.all()
        score = 0
        total_questions = questions.count()

        for question in questions:
            selected_answer_id = data.get(f'question_{question.id}')
            if selected_answer_id:
                try:
                    selected_answer = Answer.objects.get(id=selected_answer_id)
                    if selected_answer.is_correct:
                        score += 1
                except Answer.DoesNotExist:
                    pass

        # Сохраняем результат теста
        test_result, created = TestResult.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={
                'score': score,
                'total_questions': total_questions
            }
        )

        return JsonResponse({
            'score': score,
            'total_questions': total_questions,
            'percentage': test_result.get_percentage(),
            'success': True
        })

    return JsonResponse({'success': False}, status=400)

from django.contrib.auth.decorators import login_required

@login_required
def logout_confirm(request):
    return render(request, 'registration/logout_confirm.html')

def custom_logout(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            username = request.user.username
            logout(request)
            messages.info(request, f'Вы успешно вышли из системы. До свидания, {username}!')
        return redirect('courses:course_list')
    
    return redirect('courses:logout_confirm')