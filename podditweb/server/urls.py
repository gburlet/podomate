from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('guide', views.guide, name='guide'),
    path('feedback', views.feedback, name='feedback'),
    path('api/activate', views.Activate.as_view(), name="activate"),
    path('api/update', views.Update.as_view(), name="update"),
    path('api/version', views.ClientVersion.as_view(), name="version"),
]
