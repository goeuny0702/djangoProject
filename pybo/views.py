from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import openai
import os

from openai import OpenAI
from openai import OpenAIError, RateLimitError, AuthenticationError


# API 키 설정 (환경변수에서 받아오기)
openai.api_key = settings.OPENAI_API_KEY

def index(request):
    return HttpResponse("Hello, Django! 😊 여기는 홈페이지입니다.")

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
