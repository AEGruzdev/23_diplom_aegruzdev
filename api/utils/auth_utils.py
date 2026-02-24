from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


def get_user_from_token(request):
    """
    Извлечение пользователя из токена в заголовке Authorization
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Token '):
        return None
    
    token_key = auth_header.split(' ')[1]
    
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


def check_ownership(request, obj, owner_field='user'):
    """
    Проверка, является ли пользователь владельцем объекта
    """
    user = get_user_from_token(request)
    
    if not user:
        return False
    
    obj_owner = getattr(obj, owner_field, None)
    
    if hasattr(obj_owner, 'id'):
        return obj_owner.id == user.id
    elif hasattr(obj_owner, 'pk'):
        return obj_owner.pk == user.pk
    
    return obj_owner == user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешение на уровне объекта - только владельцам разрешено редактировать.
    """
    def has_object_permission(self, request, view, obj):
        # Читать разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Проверяем, является ли пользователь владельцем
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False