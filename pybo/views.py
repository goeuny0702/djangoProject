from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import openai
import os
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth import authenticate, login


from openai import OpenAI
from openai import OpenAIError, RateLimitError, AuthenticationError


# API 키 설정 (환경변수에서 받아오기)
openai.api_key = settings.OPENAI_API_KEY

def index(request):
    return HttpResponse("Hello, Django! 여기는 홈페이지입니다.")

def ai_chat(request):
    user_input = request.GET.get('q', '')

    try:
        client = OpenAI(api_key=openai.api_key)

        response: ChatCompletion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": user_input}
            ]
        )

        answer = response.choices[0].message.content
        return JsonResponse({'answer': answer}, json_dumps_params={'ensure_ascii': False})


    except RateLimitError:
        return JsonResponse({'error': '요청 한도를 초과했어요! 잠시 후 다시 시도해주세요 🥲'}, status=429)

    except AuthenticationError:
        return JsonResponse({'error': 'API 키 인증 오류입니다! 설정을 다시 확인해 주세요 🔑'}, status=401)

    except OpenAIError as e:
        return JsonResponse({'error': f'OpenAI 오류 발생: {str(e)}'}, status=500)

    except Exception as e:
        return JsonResponse({'error': f'예기치 못한 오류 발생: {str(e)}'}, status=500)
    
    
def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, '비밀번호가 일치하지 않아요.')
            return render(request, 'signup.html', {'username': username})

        if User.objects.filter(username=username).exists():
            messages.error(request, '이미 존재하는 아이디입니다.')
            return render(request, 'signup.html')

        user = User.objects.create_user(username=username, password=password1)
        login(request, user)  # 가입 후 바로 로그인 처리
        messages.success(request, f'{username}님 환영합니다 ♡')
        return redirect('home')  # 가입 후 이동할 페이지 

    return render(request, 'signup.html')    

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'{username}님 환영합니다 ♡')
            return redirect('home')  # 로그인 후 이동할 페이지
        else:
            messages.error(request, '아이디 또는 비밀번호가 틀려요.')

    return render(request, 'login.html')

def home_view(request):
    return render(request, 'home.html')


def logout_view(request):
    logout(request)
    return redirect('login')  # 로그아웃 후 로그인 페이지로 보내기