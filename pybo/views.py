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

    system_prompt = """너는 대기업 인사담당자 출신의 자기소개서 첨삭 전문가야.
    
[첨삭 원칙]
1. **두괄식 작성**: 핵심 메시지를 문단 앞에 배치
2. **STAR 기법 적용**: 상황(Situation) → 과제(Task) → 행동(Action) → 결과(Result) 구조로 경험 서술
3. **정량적 성과 강조**: 가능한 경우 수치, 퍼센트, 기간 등 구체적 데이터 추가
4. **역량 키워드 삽입**: 문제해결력, 협업능력, 리더십, 커뮤니케이션, 분석력 등 역량 키워드 자연스럽게 포함
5. **능동적 표현**: "~했습니다" 대신 "~를 주도했습니다", "~를 달성했습니다" 등 적극적 동사 사용
6. **문장 간 연결**: 접속사와 연결어를 활용해 논리적 흐름 강화
7. **분량 보강**: 내용이 부족하면 예상되는 맥락을 추가하여 풍부하게 확장 (원본 대비 1.3~1.5배)

[작성 스타일]
- 진정성 있고 구체적인 경험 중심
- 지원 직무와 연관된 역량 강조
- 읽기 쉬운 문단 구성 (한 문단 3~5문장)
- 클리셰 표현 지양 (열정, 최선, 노력 등 추상적 표현 구체화)

[출력 형식]
- 첨삭된 자기소개서 본문만 출력
- 설명이나 코멘트 없이 수정된 글만 반환
- 원본의 핵심 메시지와 경험은 유지"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"다음 자기소개서를 첨삭해줘:\n\n{text}"}
        ],
        temperature=0.4,
        max_tokens=2000
    )
    improved = resp.choices[0].message.content.strip()
    return JsonResponse({"result": improved})

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        return redirect('resume_page')

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
        pprint.pprint(request.POST)

        content_dict = {
            "name": request.POST.get("name"),
            "gender": request.POST.get("gender"),
            "birthdate": request.POST.get("birthdate"),
            "email": request.POST.get("email"),
            "phone": request.POST.get("phone"),
            "address": request.POST.get("address"),
            "detail_address": request.POST.get("detail-address"),
        }

        sections_json = request.POST.get("sections_json")
        if sections_json:
            try:
                sections_data = json.loads(sections_json)
                content_dict["sections"] = sections_data
            except Exception as e:
                print("sections_json 파싱 실패", e)

        pprint.pprint(content_dict)

        # 이미지 처리
        image_file = request.FILES.get("profile_image")
        resume = Resume.objects.create(
            user=request.user,

            title=request.POST.get("title"),
            profile_image=image_file,
            content="임시"  # 우선 임시 저장

        )

        # 이미지가 있다면 content에도 포함
        if resume.profile_image:
            content_dict["profile_image_url"] = resume.profile_image.url

        # 실제 content 저장
        resume.content = json.dumps(content_dict)
        resume.save()

        return redirect('resume_page')


@login_required
def resume_page(request):
    resumes = Resume.objects.filter(user=request.user)  # 로그인한 유저 것만
    return render(request, 'resume.html', {'resumes': resumes})


@login_required
def get_resume(request, resume_id):
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
        content_dict = json.loads(resume.content)

        resume_data = {
            'title': resume.title,
            'content': content_dict,
            'profile_image_url': resume.profile_image.url if resume.profile_image else None
        }
        return JsonResponse(resume_data)
    except Resume.DoesNotExist:
        return JsonResponse({'error': '이력서를 찾을 수 없습니다.'}, status=404)

@login_required
def preview_resume(request, resume_id):
    try:
        resume = Resume.objects.get(id=resume_id, user=request.user)
        content_dict = json.loads(resume.content)
        
        context = {
            'resume': resume,
            'content': content_dict,
            'profile_image_url': resume.profile_image.url if resume.profile_image else None
        }
        return render(request, 'pdf.html', context)
    except Resume.DoesNotExist:
        return HttpResponse('이력서를 찾을 수 없습니다.', status=404)

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

@login_required
def preview_pdf(request, resume_id):
    # 이력서 객체를 가져옴
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    content = json.loads(resume.content)
    title = resume.title

    return render(request, 'pdf.html', {
        'title': title,
        'content': content
    })


# ─────────────────── (중복 함수 제거됨 - 위에서 정의됨) ───────────────────


