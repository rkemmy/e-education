
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.validators import UniqueValidator
from eneza.authentication.models import User
from eneza.exceptions import InvalidPermissionsException, SimpleValidationError

class UserSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(
            required=True,
            validators=[UniqueValidator(queryset=User.objects.all())]
            )

    first_name=serializers.CharField(max_length=32, required=True)
    last_name=serializers.CharField(max_length=32, required = True)

    password = serializers.CharField(min_length=6, max_length=100,
            write_only=True, required = True)
    password_confirm = serializers.CharField(min_length=6, max_length=100,
            write_only=True, required = True)

    def validate(self,data):
        if data["password"] != data["password_confirm"]:
            raise SimpleValidationError(detail="Passwords Do not Match")
        return data

    def create(self,validated_data):
        try:
            validated_data.pop("password_confirm")
            user=User(email=validated_data["email"], first_name = validated_data["first_name"],last_name = validated_data["last_name"])

            user.set_password(validated_data["password"])
            user.save()
            return user
        except Exception as e:
            raise APIException("Error while creating instance: {error}".format(error=e))

    class Meta:
        model=User
        fields=["id","first_name","last_name","email","password","password_confirm"]


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField(label=_("email"))
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                
                raise SimpleValidationError(detail='Invalid Username or Password')
        else:
            msg = _('Must provide email and password')
            raise SimpleValidationError(detail=msg)

        attrs['user'] = user
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(min_length=6, max_length=100,
            write_only=True, required = True)

    new_password = serializers.CharField(min_length=6, max_length=100,
            write_only=True, required = True)

    def validate_current_password(self, value):
        user = self.context["request"].user  
        if not user.check_password(value):
            raise serializers.ValidationError(_("Invalid current password"), code="authentication")
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        new_password = validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        return True


class EditUserSerializer(serializers.Serializer):
    email = serializers.EmailField(
            validators=[UniqueValidator(queryset=User.objects.all())],
            required = False
            )
    first_name=serializers.CharField(max_length=32,required=False)
    last_name=serializers.CharField(max_length=32, required=False)

    def create(self, validated_data):
        user = self.context["request"].user
        for attr, value in validated_data.items():
            setattr(user,attr,value)
        user.save()
        return True
