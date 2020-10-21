from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('download', views.download, name='download'),
    path('guide', views.guide, name='guide'),
    path('about', views.about, name='about'),
    path('contact', views.contact, name='contact'),
    path('feedback', views.feedback, name='feedback'),
    path('api/activate', views.Activate.as_view(), name="activate"),
    path('api/update', views.Update.as_view(), name="update"),
    path('api/version', views.ClientVersion.as_view(), name="version"),
]
