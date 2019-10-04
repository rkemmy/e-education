from django.urls import path,include
from rest_framework.routers import DefaultRouter
from eneza.authentication.views import UserView


router =  DefaultRouter()

router.register(r'users', UserView, base_name="users-view")

urlpatterns=[
   path("", include(router.urls))
]