from django.shortcuts import get_object_or_404
from rest_framework import parsers, renderers
from rest_framework.authtoken.models import Token
from rest_framework.compat import coreapi, coreschema
from rest_framework.schemas import ManualSchema
from rest_framework.views import APIView
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

    @action(detail=False, methods=["GET"], permission_classes = [IsAuthenticated], name="details")
    def details(self, request):
        serializer =  UserSerializer(instance=request.user)
        return Response(serializer.data, status = status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], permission_classes = [AllowAny,], name="forgot-password")
    def forgot_password(self, request):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

    @action(detail=True, methods=["POST"], permission_classes = [IsAuthenticated,IsCurrentUser], name="change-password")
    def change_password(self, request, pk=None):
        user = self.get_user_object(pk)
        serializer = ChangePasswordSerializer(data=request.data, context={"request":request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success":"password successfully changed"},status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"], permission_classes = [IsAuthenticated,IsCurrentUser], name="edit-user")
    def edit_user(self, request, pk=None):
        user = self.get_user_object(pk)
        serializer =  EditUserSerializer(data=request.data, context={"request":request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(instance=self.get_user_object(pk)).data, status=status.HTTP_200_OK)

    def list(self, request):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

    def create(self, request):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

    def retrieve(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

    def update(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

    def partial_update(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, pk=None):
        return Response({"error":"Not Implemented"},status=status.HTTP_501_NOT_IMPLEMENTED)

class ObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer
    if coreapi is not None and coreschema is not None:
        schema = ManualSchema(
            fields=[
                coreapi.Field(
                    name="email",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="email",
                        description="Valid email for authentication",
                    ),
                ),
                coreapi.Field(
                    name="password",
                    required=True,
                    location='form',
                    schema=coreschema.String(
                        title="Password",
                        description="Valid password for authentication",
                    ),
                ),
            ],
            encoding="application/json",
        )

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})
