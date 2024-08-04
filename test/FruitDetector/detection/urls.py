from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('chat/', views.chat, name='chat'),  # Add this line for chat handling
]
