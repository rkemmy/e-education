from rest_framework import serializers
from rest_framework.exceptions import APIException
from rest_framework.validators import UniqueValidator
from eneza.authentication.models import User

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
            raise serializers.ValidationError("PASSWORD_CONFIRMATION_ERROR")
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
