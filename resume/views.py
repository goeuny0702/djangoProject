from django.shortcuts import render, redirect, get_object_or_404
from .models import Resume
from django.contrib.auth.decorators import login_required

@login_required
def create_resume(request):
    if request.method == 'POST':
        Resume.objects.create(
            user=request.user,
            title=request.POST['title'],
            name=request.POST['name'],
            birthdate=request.POST.get('birthdate'),
            email=request.POST['email'],
            phone=request.POST['phone'],
            address=request.POST['address'],
        )
        return redirect('resume_list')
    return render(request, 'resume/create.html')


@login_required
def resume_list(request):
    resumes = Resume.objects.filter(user=request.user)
    return render(request, 'resume/list.html', {'resumes': resumes})


@login_required
def resume_detail(request, id):
    resume = get_object_or_404(Resume, id=id, user=request.user)
    return render(request, 'resume/detail.html', {'resume': resume})

