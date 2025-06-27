"""
URL configuration for the gallery app
Maps URLs to views
"""

from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.home_view, name='home'),
    path('upload/', views.upload_view, name='upload'),
    path('quick-upload/', views.quick_upload_view, name='quick_upload'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('processing/', views.processing_view, name='processing'),
    path('failed/', views.failed_view, name='failed'),
    
    # Detail pages
    path('artwork/<uuid:pk>/', views.artwork_detail_view, name='artwork_detail'),
    path('artwork/<uuid:pk>/retry/', views.retry_artwork_view, name='retry_artwork'),
    

    path('batch-upload/', views.batch_upload_view, name='batch_upload'),
    path('batch/', views.batch_list_view, name='batch_list'),
    path('batch/<uuid:pk>/', views.batch_detail_view, name='batch_detail'),
    path('batch/<uuid:pk>/retry/', views.batch_retry_view, name='batch_retry'),

    # API endpoints for AJAX requests
    path('api/artwork/<uuid:pk>/status/', views.artwork_status_api, name='artwork_status_api'),
    path('api/gallery/stats/', views.gallery_stats_api, name='gallery_stats_api'),
    path('api/upload/progress/', views.upload_progress_api, name='upload_progress_api'),
    path('api/batch/<uuid:pk>/progress/', views.batch_progress_api, name='batch_progress_api'),
    path('register-admin/', views.admin_register_view, name='admin_register'),
    path('register-client/', views.client_register_view, name='client_register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),



    # urls.py
    path('artwork/delete/<uuid:artwork_id>/', views.delete_artwork, name='delete_artwork')


]