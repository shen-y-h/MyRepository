from rest_framework import serializers
from .models import User, Librarian, Book, VerificationCode, WebsiteInfo, LibrarianApplication
#from datetime import datetime,timedelta


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(
            name=validated_data['name'],
            email=validated_data['email'],
            password=validated_data['password']  # 实际项目中应该加密
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    reader_id = serializers.CharField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['reader_id', 'name', 'email', 'is_frozen', 'created_at']
        read_only_fields = ['reader_id', 'created_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['password', 'email']


class LibrarianLoginSerializer(serializers.Serializer):
    librarian_id = serializers.CharField()
    password = serializers.CharField()


class LibrarianRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibrarianApplication
        fields = ['name', 'application_reason']


class LibrarianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Librarian
        fields = ['librarian_id', 'name', 'email', 'created_at']


class BookSerializer(serializers.ModelSerializer):
    due_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Book
        fields = ['book_id', 'title', 'author', 'location_index', 'is_available',
                  'borrowed_by', 'borrow_date', 'due_date', 'created_at']


class BookCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['title', 'author', 'location_index']


class BorrowBookSerializer(serializers.Serializer):
    book_id = serializers.CharField()


class VerificationCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationCode
        fields = ['email', 'code']


class WebsiteInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteInfo
        fields = ['title', 'content', 'updated_at']


class LibrarianApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibrarianApplication
        fields = ['id', 'name', 'application_reason', 'status', 'created_at']