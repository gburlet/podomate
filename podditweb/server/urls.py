from django.urls import path, include
from rest_framework import routers

from . import views

# REST API URLs
router = routers.DefaultRouter()
#router.register(r'activate', views.)

urlpatterns = [
    path('', views.index, name='index'),
    path('api', include(router.urls)),
]
