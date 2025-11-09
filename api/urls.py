from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthViewSet, UserViewSet, LibrarianViewSet, WebsiteInfoViewSet, PasswordResetViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'user', UserViewSet, basename='user')
router.register(r'librarian', LibrarianViewSet, basename='librarian')
router.register(r'website', WebsiteInfoViewSet, basename='website')
router.register(r'password', PasswordResetViewSet, basename='password')

urlpatterns = [
    path('api/', include(router.urls)),
]