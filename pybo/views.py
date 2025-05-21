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
from .models import Resume
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
import pprint

from openai import OpenAI
from openai import OpenAIError, RateLimitError, AuthenticationError

# API 키 설정 (환경변수에서 받아오기)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─────────────────── 맞춤법 ───────────────────
@csrf_exempt
@require_POST
def spellcheck(request):
    text = json.loads(request.body).get("text", "")

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"너는 한국어 교정 도우미야. 맞춤법·띄어쓰기·오탈자만 고쳐서 원문 형식 그대로 돌려줘."},
            {"role":"user",  "content":text}
        ],
        temperature=0
    )
    corrected = resp.choices[0].message.content.strip()
    return JsonResponse({"result": corrected})

# ─────────────────── AI 첨삭 ───────────────────
@csrf_exempt
@require_POST
def proofread(request):
    text = json.loads(request.body).get("text", "")

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":(
              "너는 인사담당자 관점의 첨삭 코치야. 문맥은 유지하되 "
              "① 맞춤법 ② 문장 간 흐름 ③ 구체적·적극적 어휘 제안 세가지를 반영해 "
              "수정본만 돌려줘."
              "직업에 따른 전문용어를 포함해서 작성해줘"
            )},
            {"role":"user","content":text}
        ],
        temperature=0.3
    )
    improved = resp.choices[0].message.content.strip()
    return JsonResponse({"result": improved})

def ai_chat(request):
    user_input = request.GET.get('q', '')

    try:
        client = OpenAI(api_key=openai.api_key)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": user_input}
            ]
        )

        answer = response.choices[0].message.content
        return JsonResponse({'answer': answer}, json_dumps_params={'ensure_ascii': False})

    except RateLimitError:
        return JsonResponse({'error': '요청 한도를 초과했어요! 잠시 후 다시 시도해주세요'}, status=429)

    except AuthenticationError:
        return JsonResponse({'error': 'API 키 인증 오류입니다! 설정을 다시 확인해 주세요'}, status=401)

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
        return redirect('login')

    return render(request, 'signup.html')    

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # messages.success(request, f'{username}님 환영합니다 ♡')
            return redirect('resume_page')
        else:
            messages.error(request, '아이디 또는 비밀번호가 틀려요.')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def save_resume(request):
    if request.method == 'POST':
        import pprint
        # pprint.pprint(request.POST)   # 1) sections_json 실제로 오는지 확인

        content_dict = {
            "name": request.POST.get("name"),
            "gender": request.POST.get("gender"),
            "birthdate": request.POST.get("birthdate"),
            "email": request.POST.get("email"),
            "phone": request.POST.get("phone"),
            "address": request.POST.get("address"),
            "detail_address": request.POST.get("detail-address"),
            "skills": json.loads(request.POST.get("skills", "[]")), # skills 데이터 파싱
        }

        # 각 섹션별 데이터 파싱 및 추가
        sections_to_process = [
            ("education", "education"),
            ("career", "career"),
            ("experience", "experience"),
            ("certificates", "certificates"),
            ("preferences", "preferences"),
            ("portfolios", "portfolios"),
            ("career_descriptions", "career_descriptions"),
            ("introduction", "introduction"),
        ]

        for field_name, dict_key in sections_to_process:
            data_json = request.POST.get(field_name)
            if data_json:
                try:
                    content_dict[dict_key] = json.loads(data_json)
                except json.JSONDecodeError as e:
                    print(f"{field_name} JSON 파싱 실패: {e}")
                    content_dict[dict_key] = [] # 파싱 실패 시 빈 리스트 할당 또는 오류 처리

        # pprint.pprint(content_dict)  # 저장 직전 실제로 skills, sections 찍힘?

        # Resume.objects.create(
        #     user=request.user,
        #     title=request.POST.get("title"),
        #     content=json.dumps(content_dict) # content 전체를 JSON 문자열로 저장
        # )
        
        # 기존 이력서가 있으면 업데이트, 없으면 생성
        resume_title = request.POST.get("title")
        resume_instance, created = Resume.objects.update_or_create(
            user=request.user,
            title=resume_title,
            defaults={'content': json.dumps(content_dict)}
        )

        return redirect('resume_page')


@login_required
def resume_page(request):
    resumes = Resume.objects.filter(user=request.user)  # 로그인한 유저 것만
    return render(request, 'resume.html', {'resumes': resumes})


@login_required
def get_resume(request, resume_id):
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
        resume_data = {
            'title': resume.title,
            'content': json.loads(resume.content)  # content 전체를 dict로 전달
        }
        return JsonResponse(resume_data)
    except Resume.DoesNotExist:
        return JsonResponse({'error': '이력서를 찾을 수 없습니다.'}, status=404)


    
@login_required
@csrf_exempt
def delete_resume(request, resume_id):
    if request.method == 'POST':
        try:
            resume = Resume.objects.get(id=resume_id, user=request.user)
            resume.delete()
            return JsonResponse({'success': True})
        except Resume.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Resume not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


    
