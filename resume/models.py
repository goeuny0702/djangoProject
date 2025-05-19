# resume/models.py 예시
from django.db import models

class Resume(models.Model):
    name = models.CharField(max_length=100)
    # 기타 필드 정의...
