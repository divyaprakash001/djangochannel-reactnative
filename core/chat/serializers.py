from rest_framework import serializers
from .models import User, Connection

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
    if obj.pending_them:
      return 'pending-them'
    elif obj.pending_me:
      return 'pending-me'
    elif obj.connected:
      return 'connected'
    else:
      return 'no-connection'
  

class RequestSerializer(serializers.ModelSerializer):
  sender = UserSerializer()
  receiver = UserSerializer()

  class Meta:
    model = Connection
    fields = [
      'id',
      'sender',
      'receiver',
      'created',
      'updated'
    ]


class FriendSerializer(serializers.ModelSerializer):
  friend = serializers.SerializerMethodField()
  preview = serializers.SerializerMethodField()

  class Meta:
    model = Connection
    fields = [
			'id',
			'friend',
			'preview',
			'updated'
		]
  
  def get_friend(self,obj):
    # if i am the sender
    if self.context['user'] == obj.sender:
      return UserSerializer(obj.receiver).data
    # if i am the receiver
    elif self.context['user'] == obj.receiver:
      return UserSerializer(obj.sender).data
    else:
      print("Error :: No user found in friendseralizer")

  def get_preview(self,data):
    return 'New Connection'
  
 
