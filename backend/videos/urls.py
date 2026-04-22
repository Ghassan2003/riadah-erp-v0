"""
URL patterns لنظام تعليمات الفيديو.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.VideoCategoryViewSet, basename='video-categories')
router.register(r'videos', views.VideoInstructionViewSet, basename='video-instructions')

urlpatterns = [
    # Router URLs (ViewSets)
    path('', include(router.urls)),

    # تقدم المشاهدة
    path('progress/', views.VideoProgressView.as_view(), name='video-progress'),
    path('progress/<int:video_id>/', views.VideoProgressDetailView.as_view(), name='video-progress-detail'),

    # التعليقات
    path('<int:video_id>/comments/', views.VideoCommentListCreateView.as_view(), name='video-comments'),
    path('comments/<int:pk>/', views.VideoCommentDetailView.as_view(), name='video-comment-detail'),
    path('comments/<int:pk>/update/', views.VideoCommentUpdateView.as_view(), name='video-comment-update'),
    path('comments/<int:pk>/delete/', views.VideoCommentDeleteView.as_view(), name='video-comment-delete'),

    # البحث
    path('search/', views.VideoSearchView.as_view(), name='video-search'),
]
