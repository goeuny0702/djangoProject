"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from pybo import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# from resume import views



urlpatterns = [
    path("admin/", admin.site.urls),
    path("ai_chat/", views.ai_chat, name="ai_chat"),
    path('signup/', views.signup_view, name='signup'),  # 회원가입
    path('', views.login_view, name='login'),  # 로그인
    path('logout/', views.logout_view, name='logout'),  # 로그아웃
    path('resume/', views.resume_page, name='resume_page'),  # 이력서
    path('save_resume/', views.save_resume, name='save_resume'),
    path('get_resume/<int:resume_id>/', views.get_resume, name='get_resume'),
    path('resume/delete/<int:resume_id>/', views.delete_resume, name='delete_resume'),
    path('resume/preview/<int:resume_id>/', views.preview_resume, name='preview_resume'),  # 이력서 미리보기
    path("api/spellcheck/", views.spellcheck, name="spellcheck"),
    path("api/proofread/",  views.proofread,  name="proofread"),

] 


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

