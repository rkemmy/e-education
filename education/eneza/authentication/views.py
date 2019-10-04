from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, BasePermission,IsAuthenticated
from rest_framework import status
from rest_framework.decorators import action

from eneza.authentication.serializers import UserSerializer, AuthTokenSerializer,\
                             ChangePasswordSerializer, EditUserSerializer
from eneza.authentication.models import User

class IsCurrentUser(BasePermission):
    def has_permission(self, request, view):
        pk = pk=view.kwargs.get('pk',None)
        user = get_object_or_404(User,pk=pk )
        return request.user == user

class UserView(ViewSet):
    permission_classes=[AllowAny,]

    def get_user_object(self,pk):
        user = get_object_or_404(User , pk=pk)
        return user

    @action(detail=False, methods=['POST'], permission_classes=[AllowAny,], name="sign-up")
    def sign_up(self, request):
        serializer=UserSerializer(data=request.data, context={"request":request})
        if serializer.is_valid():
            user=serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["GET"], permission_classes = [IsAuthenticated, IsCurrentUser], name="details")
    def details(self, request, pk=None):
        user = self.get_user_object(pk)
        serializer =  UserSerializer(instance=user)
        return Response(serializer.data, status = status.HTTP_200_OK)
