from rest_framework.views import APIView
import http
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from chat.serializers import SignUpSerializer, UserSerializer


class Home(APIView):
  permission_classes=[AllowAny]

  def get(self,request):
    return Response({'message':'Home Page','status':200})