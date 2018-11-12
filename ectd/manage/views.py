#from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, status
from rest_framework.views import APIView
from ectd.manage.serializers import UserSerializer, GroupSerializer, PasswordSerializer, AccountSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny, IsAdminUser
from ectd.extra.msg import Msg
import re
from django.db import IntegrityError
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
# from django.contrib.auth.tokens import default_token_generator
from ectd.extra.tokens import account_activation_token
from ectd.applications.models import Employee
from ectd.applications.serializers import EmployeeSerializer
# class IsAdminOrIsSelf(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         if request.user.is_superuser:
#             return True
#         return obj.username == request.user

class UserViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """
    def list(self, request):
        
        if request.user.is_superuser:
            queryset = User.objects.all()
            serializer = UserSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or request.user == user:
            serializer = UserSerializer(user)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    def update(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data)
        if request.user.is_superuser or request.user == user:
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def destroy(self, request, pk=None):
        if  not request.user.is_superuser:
           return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION) 
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['post'], detail=True,)
    def set_password(self, request, pk=None):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        if request.user.is_superuser or request.user == user:
            serializer = PasswordSerializer(data=request.data)
            if serializer.is_valid():
                user.set_password(serializer.data['password'])
                user.save()
                return Response({'msg': 'password set'})
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    @action(methods=['get'], detail=True, permission_classes=(IsAdminUser,))
    def activate(self, request, pk=None):
        
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        
        user.is_active = True
        user.save()
        return Response({'msg': 'Account activated'})

class Verify(APIView):
    def get(self, request, format=None):
        try: 
            employee = Employee.objects.get(user = request.user)
            serializer = EmployeeSerializer(employee)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)

class AccountList(APIView):
    permission_classes = (AllowAny ,)

    def post(self, request, format=None):
        if not re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", request.data['username']):
            return Response({'msg': 'Email invalid'}, status=status.HTTP_400_BAD_REQUEST)
        request.data['is_active'] = False
        request.data['email']=request.data['username']
        try:
            user = User.objects.create_user(**request.data)
            self.send_email(user, request)
            return Response({'msg': 'Account created'}, status=status.HTTP_201_CREATED)
        except(ValueError, User.DoesNotExist):
            return Response({'msg': 'error'}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({'msg': 'Email alread exist'}, status=status.HTTP_400_BAD_REQUEST)
        # serializer = AccountSerializer(data=request.data)
        # if serializer.is_valid():
        #     user = User(**serializer.validated_data)
        #     serializer.save()
        #     print(user.id)
        #     self.send_email(user, request)
        #     return Response({'msg': 'Account created'}, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def send_email(self, user, request):
        current_site = get_current_site(request)
        mail_subject = 'Activate your account.'   
        print(user.pk, user.email)
        message = render_to_string('activate_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(), #urlsafe_base64_encode(force_bytes(user.pk)),
            'token':account_activation_token.make_token(user),
        })
        
        to_email = request.data['email']
        email = EmailMessage( mail_subject, message, to=[to_email])
        email.send()

class ActivateAccount(APIView):
    permission_classes = (AllowAny ,)

    def post(self, request, format=None):
        try:
            uid = force_text(urlsafe_base64_decode(request.data['uid']))
            user = User.objects.get(pk=uid)
            print(user.pk, user.email)
            if account_activation_token.check_token(user, request.data['token']):
                user.is_active = True
                user.save()
                return Response({'msg': 'Account activated'})
            else:
                return Response({'msg':'Activation link is invalid!'}, status=status.HTTP_400_BAD_REQUEST)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'msg':'error'}, status=status.HTTP_400_BAD_REQUEST)

class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser ,)
    queryset = Group.objects.all()
    serializer_class = GroupSerializer



