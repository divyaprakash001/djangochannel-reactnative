from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
  name = serializers.SerializerMethodField()
  class Meta:
    model = User
    fields = ['username',
              'name',
              'thumbnail'
              ]
  
  def get_name(self,obj):
    fname = obj.first_name.capitalize()
    lname = obj.last_name.capitalize()
    return fname + ' ' + lname
  

class SignUpSerializer(serializers.ModelSerializer):
  class Meta:
    model=User
    fields=[
      'username',
			'first_name',
			'last_name',
			'password'
    ]
    extra_kwargs = {
			'password': {
				# Ensures that when serializing, this field will be excluded
				'write_only': True
			}
		}

  def create(self, validated_data):
    username = validated_data['username']
    first_name = validated_data['first_name']
    last_name = validated_data['last_name']

    user = User.objects.create(
      username=username,
      first_name=first_name,
      last_name=last_name
    )
    password = validated_data['password']
    user.set_password(password)
    user.save()
    return user
  

class SearchSerializer(UserSerializer):
  status = serializers.SerializerMethodField()

  class Meta:
    model=User
    fields=[
      'username',
      'name',
      'thumbnail',
      'status'
    ]
  
  def get_status(self,obj):
    return 'no-connection'