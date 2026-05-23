from django.urls import path
from .enhanced_views import (
    EducationListView, EducationCreateView,
    ExperienceListView, ExperienceCreateView,
    SkillListView, SkillCreateView,
    LanguageListView, LanguageCreateView,
    CertificationListView, CertificationCreateView,
)

urlpatterns = [
    path('education/', EducationListView.as_view(), name='education-list'),
    path('education/create/', EducationCreateView.as_view(), name='education-create'),
    path('experience/', ExperienceListView.as_view(), name='experience-list'),
    path('experience/create/', ExperienceCreateView.as_view(), name='experience-create'),
    path('skills/', SkillListView.as_view(), name='skill-list'),
    path('skills/create/', SkillCreateView.as_view(), name='skill-create'),
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('languages/create/', LanguageCreateView.as_view(), name='language-create'),
    path('certifications/', CertificationListView.as_view(), name='certification-list'),
    path('certifications/create/', CertificationCreateView.as_view(), name='certification-create'),
]
