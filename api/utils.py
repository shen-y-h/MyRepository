import jwt
from django.conf import settings
from datetime import datetime,timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import logging

logger = logging.getLogger(__name__)

def generate_jwt_token(payload):
    payload['exp'] = datetime.now(timezone.utc) + settings.JWT_EXPIRATION_DELTA
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token

def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception('Token expired')
    except jwt.InvalidTokenError:
        raise Exception('Invalid token')


class JWTAuthentication(BaseAuthentication):
    """JWT认证类"""

    def authenticate(self, request):
        # 从请求头中获取token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header:
            return None

        # 检查token格式
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]

        try:
            # 验证token
            payload = verify_jwt_token(token)

            # 根据token类型返回对应的用户
            if payload.get('type') == 'user':
                from .models import User
                user = User.objects.get(reader_id=payload['reader_id'])
                return (user, token)
            elif payload.get('type') == 'librarian':
                from .models import Librarian
                user = Librarian.objects.get(librarian_id=payload['librarian_id'])
                return (user, token)
            else:
                raise AuthenticationFailed('Invalid token type')

        except Exception as e:
            logger.error(f"JWT authentication failed: {e}")
            raise AuthenticationFailed('Authentication failed')