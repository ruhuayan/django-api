#from django.shortcuts import render

from django.contrib.auth.models import User, Group
from rest_framework import viewsets, status
from rest_framework.views import APIView
from ectd.manage.serializers import UserSerializer, GroupSerializer, PasswordSerializer, AccountSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404
from ectd.extra.msg import Msg

from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from ectd.extra.tokens import account_activation_token
# class IsAdminOrIsSelf(BasePermission):
#     def has_object_permission(self, request, view, obj):
#         if request.user.is_superuser:
#             return True
#         return obj.username == request.user

class UserViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """
    # permission_classes = (AllowAny ,)
    def list(self, request):
        
        if request.user.is_superuser:
            queryset = User.objects.all()
            serializer = UserSerializer(queryset, many=True)
            return Response(serializer.data)
        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

    def retrieve(self, request, pk=None):
        # queryset = User.objects.all()
        # user = get_object_or_404(queryset, pk=pk)
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(Msg.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        if request.user.is_superuser or request.user == user:
            serializer = UserSerializer(user)
            return Response(serializer.data)

        return Response(Msg.NOT_AUTH, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
    
    # def create(self, request):
    #     serializer = UserSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

class AccountList(APIView):
    permission_classes = (AllowAny ,)

    def post(self, request, format=None):
        request.data['is_active'] = False
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            user = User(**serializer.validated_data)
            self.send_email(user, request)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=True, )
    def activate(self, request, uid=None, token=None):  # does not work
        print(uid)
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except(TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'msg': 'Thank you for your email confirmation. Now you can login your account.'})
        else:
            return Response({'msg':'Activation link is invalid!'}, status=status.HTTP_400_BAD_REQUEST)

    def send_email(self, user, request):
        current_site = get_current_site(request)
        mail_subject = 'Activate your account.'
        uid = urlsafe_base64_encode(force_bytes(user.pk)).decode("utf-8")
     
        message = render_to_string('activate_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token':account_activation_token.make_token(user),
        })
        
        #message='http://'+current_site.domain+'/users/register/activate/'+uid+'/'+account_activation_token.make_token(user)
        to_email = request.data['email']
        email = EmailMessage(
                    mail_subject, message, to=[to_email]
        )
        email.send()



class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser ,)
    queryset = Group.objects.all()
    serializer_class = GroupSerializer



