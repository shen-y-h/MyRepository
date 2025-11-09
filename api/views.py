from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import random
import string


from .serializers import *
from .utils import generate_jwt_token, verify_jwt_token


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def user_register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': '注册成功',
                'reader_id': user.reader_id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def user_login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            reader_id = serializer.validated_data['reader_id']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(reader_id=reader_id, password=password)
                if user.is_frozen:
                    return Response({'error': '账号已被冻结，无法借书'}, status=status.HTTP_403_FORBIDDEN)

                token = generate_jwt_token({'reader_id': user.reader_id, 'type': 'user'})
                return Response({
                    'token': token,
                    'user': UserSerializer(user).data
                })
            except User.DoesNotExist:
                return Response({'error': '读者证号或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def librarian_login(self, request):
        serializer = LibrarianLoginSerializer(data=request.data)
        if serializer.is_valid():
            librarian_id = serializer.validated_data['librarian_id']
            password = serializer.validated_data['password']

            try:
                librarian = Librarian.objects.get(librarian_id=librarian_id, password=password)
                token = generate_jwt_token({'librarian_id': librarian.librarian_id, 'type': 'librarian'})
                return Response({
                    'token': token,
                    'librarian': LibrarianSerializer(librarian).data
                })
            except Librarian.DoesNotExist:
                return Response({'error': '管理员ID或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def librarian_register(self, request):
        serializer = LibrarianRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            application = serializer.save()
            return Response({
                'message': '申请已提交，等待审核',
                'application_id': application.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_user_from_token(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
        payload = verify_jwt_token(token)
        if payload.get('type') != 'user':
            return None
        try:
            return User.objects.get(reader_id=payload['reader_id'])
        except User.DoesNotExist:
            return None

    @action(detail=False, methods=['get'])
    def profile(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        borrowed_books = Book.objects.filter(borrowed_by=user)
        book_data = BookSerializer(borrowed_books, many=True).data

        return Response({
            'user': UserSerializer(user).data,
            'borrowed_books': book_data
        })

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': '个人信息更新成功'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def borrow_book(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_frozen:
            return Response({'error': '账号已被冻结，无法借书'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BorrowBookSerializer(data=request.data)
        if serializer.is_valid():
            book_id = serializer.validated_data['book_id']
            try:
                book = Book.objects.get(book_id=book_id)
                if not book.is_available:
                    return Response({'error': '该书已被借出'}, status=status.HTTP_400_BAD_REQUEST)

                book.is_available = False
                book.borrowed_by = user
                book.borrow_date = timezone.now()
                book.save()

                return Response({'message': '借书成功'})
            except Book.DoesNotExist:
                return Response({'error': '图书不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def return_book(self, request):
        user = self.get_user_from_token(request)
        if not user:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BorrowBookSerializer(data=request.data)
        if serializer.is_valid():
            book_id = serializer.validated_data['book_id']
            try:
                book = Book.objects.get(book_id=book_id, borrowed_by=user)
                book.is_available = True
                book.borrowed_by = None
                book.borrow_date = None
                book.save()

                return Response({'message': '还书成功'})
            except Book.DoesNotExist:
                return Response({'error': '图书不存在或不是您借阅的'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def search_books(self, request):
        query = request.GET.get('q', '')
        books = Book.objects.filter(title__icontains=query)
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)


class LibrarianViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_librarian_from_token(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
        payload = verify_jwt_token(token)
        if payload.get('type') != 'librarian':
            return None
        try:
            return Librarian.objects.get(librarian_id=payload['librarian_id'])
        except Librarian.DoesNotExist:
            return None

    @action(detail=False, methods=['get'])
    def search_users(self, request):
        librarian = self.get_librarian_from_token(request)
        if not librarian:
            return Response({'error': '管理员不存在'}, status=status.HTTP_404_NOT_FOUND)

        query = request.GET.get('q', '')
        users = User.objects.filter(name__icontains=query)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def freeze_user(self, request):
        librarian = self.get_librarian_from_token(request)
        if not librarian:
            return Response({'error': '管理员不存在'}, status=status.HTTP_404_NOT_FOUND)

        reader_id = request.data.get('reader_id')
        try:
            user = User.objects.get(reader_id=reader_id)
            user.is_frozen = True
            user.save()
            return Response({'message': '用户借书功能已冻结'})
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def unfreeze_user(self, request):
        librarian = self.get_librarian_from_token(request)
        if not librarian:
            return Response({'error': '管理员不存在'}, status=status.HTTP_404_NOT_FOUND)

        reader_id = request.data.get('reader_id')
        try:
            user = User.objects.get(reader_id=reader_id)
            user.is_frozen = False
            user.save()
            return Response({'message': '用户借书功能已解冻'})
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def add_book(self, request):
        librarian = self.get_librarian_from_token(request)
        if not librarian:
            return Response({'error': '管理员不存在'}, status=status.HTTP_404_NOT_FOUND)

        serializer = BookCreateSerializer(data=request.data)
        if serializer.is_valid():
            book = serializer.save()
            return Response({
                'message': '图书添加成功',
                'book_id': book.book_id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['put'])
    def update_book(self, request):
        librarian = self.get_librarian_from_token(request)
        if not librarian:
            return Response({'error': '管理员不存在'}, status=status.HTTP_404_NOT_FOUND)

        book_id = request.data.get('book_id')
        try:
            book = Book.objects.get(book_id=book_id)
            serializer = BookCreateSerializer(book, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'message': '图书信息更新成功'})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Book.DoesNotExist:
            return Response({'error': '图书不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def applications(self, request):
        librarian = self.get_librarian_from_token(request)
        if not librarian:
            return Response({'error': '管理员不存在'}, status=status.HTTP_404_NOT_FOUND)

        applications = LibrarianApplication.objects.filter(status='pending')
        serializer = LibrarianApplicationSerializer(applications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def approve_application(self, request):
        librarian = self.get_librarian_from_token(request)
        if not librarian:
            return Response({'error': '管理员不存在'}, status=status.HTTP_404_NOT_FOUND)

        application_id = request.data.get('application_id')
        try:
            application = LibrarianApplication.objects.get(id=application_id)
            application.status = 'approved'
            application.save()

            # 创建管理员账号
            librarian = Librarian.objects.create(
                name=application.name,
                password=str(random.randint(100000, 999999)),  # 随机生成初始密码
                email=f"{application.name}@library.com"  # 实际项目中应该要求提供邮箱
            )

            return Response({
                'message': '申请已批准',
                'librarian_id': librarian.librarian_id,
                'password': librarian.password
            })
        except LibrarianApplication.DoesNotExist:
            return Response({'error': '申请不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def reject_application(self, request):
        librarian = self.get_librarian_from_token(request)
        if not librarian:
            return Response({'error': '管理员不存在'}, status=status.HTTP_404_NOT_FOUND)

        application_id = request.data.get('application_id')
        try:
            application = LibrarianApplication.objects.get(id=application_id)
            application.status = 'rejected'
            application.save()
            return Response({'message': '申请已拒绝'})
        except LibrarianApplication.DoesNotExist:
            return Response({'error': '申请不存在'}, status=status.HTTP_404_NOT_FOUND)


class WebsiteInfoViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def get_info(self, request):
        try:
            info = WebsiteInfo.objects.first()
            if info:
                serializer = WebsiteInfoSerializer(info)
                return Response(serializer.data)
            return Response({'title': '图书管理系统', 'content': '欢迎使用图书管理系统'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def update_info(self, request):
        # 这里应该检查权限，只有管理员可以修改
        token = request.META.get('HTTP_AUTHORIZATION', '').split(' ')[1]
        payload = verify_jwt_token(token)
        if payload.get('type') != 'librarian':
            return Response({'error': '无权限'}, status=status.HTTP_403_FORBIDDEN)

        info, created = WebsiteInfo.objects.get_or_create(id=1)
        serializer = WebsiteInfoSerializer(info, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': '网站信息更新成功'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def send_code(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': '邮箱不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成6位随机验证码
        code = ''.join(random.choices(string.digits, k=6))
        expires_at = timezone.now() + timedelta(minutes=10)

        # 删除该邮箱之前的验证码
        VerificationCode.objects.filter(email=email).delete()

        # 创建新的验证码
        VerificationCode.objects.create(
            email=email,
            code=code,
            expires_at=expires_at
        )

        # 这里应该调用邮件服务发送验证码
        # send_email(email, code)

        return Response({'message': '验证码已发送'})

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')

        if not all([email, code, new_password]):
            return Response({'error': '参数不完整'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            verification = VerificationCode.objects.get(email=email, code=code)
            if not verification.is_valid():
                return Response({'error': '验证码已过期'}, status=status.HTTP_400_BAD_REQUEST)

            # 更新用户密码
            try:
                user = User.objects.get(email=email)
                user.password = new_password
                user.save()

                # 删除已使用的验证码
                verification.delete()

                return Response({'message': '密码重置成功'})
            except User.DoesNotExist:
                return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        except VerificationCode.DoesNotExist:
            return Response({'error': '验证码错误'}, status=status.HTTP_400_BAD_REQUEST)