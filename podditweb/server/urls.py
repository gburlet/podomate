from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('api/activate', views.Activate.as_view(), name="activate"),
]
