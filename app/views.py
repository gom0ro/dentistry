from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout 
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Answer, Course, Lesson, TestResult, UserCourseAccess, UserProgress, Question  # Добавлен Question
from django.db.models import Q
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from .models import CourseApplication, Course
from .forms import CourseApplicationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def home(request):
    courses = Course.objects.filter(is_active=True)
    user_has_access = []

    if request.user.is_authenticated:
        user_has_access = UserCourseAccess.objects.filter(
            user=request.user,
            is_active=True
        ).values_list('course_id', flat=True)

    return render(request, 'app/home.html', {
        'courses': courses,
        'user_has_access': user_has_access
    })

def search_courses(request):
    query = request.GET.get('q', '')  # получаем параметр ?q=
    results = []

    if query:
        results = Course.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'app/search.html', context)

def base(request):
    return render(request, 'app/base.html')

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

    # Получаем тест к уроку (если есть)
    questions = lesson.questions.all().prefetch_related('answers')

    return render(request, 'courses/lesson_detail.html', {
        'lesson': lesson,
        'questions': questions
    })

@login_required
def lesson_test(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    questions = lesson.questions.all().prefetch_related('answers')
    
    # Получаем предыдущий результат теста
    completed_test = None
    if request.user.is_authenticated:
        completed_test = TestResult.objects.filter(
            user=request.user, 
            lesson=lesson
        ).first()
    
    context = {
        'lesson': lesson,
        'questions': questions,
        'completed_test': completed_test,
    }
    return render(request, 'courses/lesson_test.html', context)

@login_required
@csrf_exempt
def submit_test(request, lesson_id):
    if request.method == 'POST':
        try:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            
            # Проверяем доступ пользователя
            if not UserCourseAccess.objects.filter(user=request.user, course=lesson.course, is_active=True).exists():
                return JsonResponse({
                    'success': False, 
                    'error': 'Нет доступа к этому курсу'
                })
            
            # Получаем данные
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON format'
                })
            
            user_answers = data.get('answers', {})
            
            questions = Question.objects.filter(lesson=lesson).prefetch_related('answers')
            total_questions = questions.count()
            correct_answers = 0
            
            detailed_results = []
            
            for question in questions:
                user_answer_id = user_answers.get(str(question.id))
                correct_answer = question.answers.filter(is_correct=True).first()
                
                user_answer_text = 'Не ответил'
                correct_answer_text = 'Нет правильного ответа'
                is_correct = False
                
                if user_answer_id:
                    try:
                        user_answer = Answer.objects.get(id=user_answer_id, question=question)
                        user_answer_text = user_answer.text
                        if user_answer.is_correct:
                            correct_answers += 1
                            is_correct = True
                    except Answer.DoesNotExist:
                        user_answer_text = 'Неверный ID ответа'
                
                if correct_answer:
                    correct_answer_text = correct_answer.text
                
                detailed_results.append({
                    'question_id': question.id,
                    'question_text': question.text,
                    'user_answer': user_answer_text,
                    'correct_answer': correct_answer_text,
                    'is_correct': is_correct
                })
            
            # Рассчитываем результат
            percentage = round((correct_answers / total_questions) * 100, 1) if total_questions > 0 else 0
            passed = percentage >= 80
            
            # Сохраняем результат
            test_result, created = TestResult.objects.update_or_create(
                user=request.user,
                lesson=lesson,
                defaults={
                    'score': percentage,
                    'correct_answers': correct_answers,
                    'total_questions': total_questions,
                    'passed': passed
                }
            )
            
            # Возвращаем успешный ответ
            response_data = {
                'success': True,
                'score': float(percentage),
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'passed': bool(passed),
                'detailed_results': detailed_results
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            import traceback
            print("Error in submit_test:", traceback.format_exc())  # Для отладки
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST method allowed'
    })

@login_required
def test_result_view(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    result = TestResult.objects.filter(
        user=request.user, 
        lesson=lesson
    ).order_by('-completed_at').first()
    
    context = {
        'lesson': lesson,
        'result': result,
    }
    
    return render(request, 'courses/test_result.html', context)

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

def course_application(request, course_id=None):
    """
    Обработка заявки на курс
    """
    # Если передан course_id, предварительно выбираем курс
    initial = {}
    if course_id:
        course = get_object_or_404(Course, id=course_id)
        initial['course'] = course
    
    if request.method == 'POST':
        form = CourseApplicationForm(request.POST, initial=initial)
        if form.is_valid():
            try:
                application = form.save()
                
                # AJAX запрос
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.'
                    })
                else:
                    messages.success(request, 'Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.')
                    return redirect('courses:course_list')  # Или другая страница
                    
            except Exception as e:
                # Ошибка при сохранении
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Ошибка при сохранении заявки'
                    }, status=500)
                else:
                    messages.error(request, 'Произошла ошибка при отправке заявки.')
        else:
            # Форма невалидна
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.get_json_data()
                }, status=400)
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = CourseApplicationForm(initial=initial)
    
    # Для GET запроса
    courses = Course.objects.all()
    return render(request, 'courses/application_form.html', {
        'form': form,
        'courses': courses,
        'selected_course_id': course_id
    })

def applications_dashboard(request):
    """Админ-панель для просмотра заявок"""
    if not request.user.is_staff:
        messages.error(request, 'Доступ запрещен.')
        return redirect('courses:course_list')
    
    applications = CourseApplication.objects.all().select_related('course').order_by('-created_at')
    
    # Статистика
    new_count = applications.filter(status='new').count()
    processed_count = applications.filter(status='processed').count()
    completed_count = applications.filter(status='completed').count()
    rejected_count = applications.filter(status='rejected').count()
    
    # Фильтрация
    status_filter = request.GET.get('status')
    course_filter = request.GET.get('course')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    if course_filter:
        applications = applications.filter(course_id=course_filter)
    
    courses = Course.objects.all()
    
    context = {
        'applications': applications,
        'new_applications_count': new_count,
        'processed_applications_count': processed_count,
        'completed_applications_count': completed_count,
        'rejected_applications_count': rejected_count,
        'courses': courses,
        'current_status': status_filter,
        'current_course': course_filter,
    }
    
    return render(request, 'courses/applications.html', context)

def update_application_status(request, application_id):
    """Обновление статуса заявки (AJAX)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Доступ запрещен'})
    
    if request.method == 'POST':
        try:
            application = CourseApplication.objects.get(id=application_id)
            new_status = request.POST.get('status')
            
            if new_status in dict(CourseApplication.STATUS_CHOICES):
                application.status = new_status
                application.save()
                
                return JsonResponse({
                    'success': True,
                    'message': f'Статус заявки обновлен на "{application.get_status_display()}"'
                })
            else:
                return JsonResponse({'success': False, 'error': 'Неверный статус'})
                
        except CourseApplication.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Заявка не найдена'})
    
    return JsonResponse({'success': False, 'error': 'Неверный метод запроса'})

@login_required
def course_progress_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Проверяем доступ пользователя к курсу
    if not UserCourseAccess.objects.filter(user=request.user, course=course, is_active=True).exists():
        messages.error(request, 'У вас нет доступа к этому курсу.')
        return redirect('courses:profile')
    
    lessons = course.lessons.all().order_by('order')
    lesson_progress = []
    
    completed_lessons = 0
    total_score = 0
    test_count = 0
    
    for lesson in lessons:
        progress = UserProgress.objects.filter(user=request.user, lesson=lesson).first()
        test_result = TestResult.objects.filter(user=request.user, lesson=lesson).first()
        
        # Считаем статистику
        if progress and progress.is_completed:
            completed_lessons += 1
        
        if test_result:
            total_score += test_result.score
            test_count += 1
        
        lesson_progress.append({
            'lesson': lesson,
            'is_completed': progress.is_completed if progress else False,
            'test_result': test_result,
            'completed_at': progress.completed_at if progress else None
        })
    
    # Вычисляем статистику
    total_lessons = lessons.count()
    pending_lessons = total_lessons - completed_lessons
    
    # Средний результат тестов
    average_score = 0
    if test_count > 0:
        average_score = round(total_score / test_count, 1)
    
    # Общий прогресс (процент завершенных уроков)
    overall_progress = 0
    if total_lessons > 0:
        overall_progress = round((completed_lessons / total_lessons) * 100, 1)
    
    # Находим следующий урок для продолжения
    next_lesson = None
    for lesson in lessons:
        progress = UserProgress.objects.filter(user=request.user, lesson=lesson).first()
        if not progress or not progress.is_completed:
            next_lesson = lesson
            break
    
    context = {
        'course': course,
        'lesson_progress': lesson_progress,
        'completed_lessons': completed_lessons,
        'pending_lessons': pending_lessons,
        'average_score': average_score,
        'overall_progress': overall_progress,
        'next_lesson': next_lesson,
    }
    return render(request, 'courses/course_progress.html', context)