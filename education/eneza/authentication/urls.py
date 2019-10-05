from django.urls import path,include
from rest_framework.routers import DefaultRouter
from tutorials_tube.authentication.views import UserView, ObtainAuthToken


router =  DefaultRouter()

router.register(r'users',UserView,base_name="users-view")

urlpatterns=[
   path("", include(router.urls)),
    path("token/login",ObtainAuthToken.as_view(), name="api-token-login"),

]