from django.db import models
import uuid
from datetime import datetime, timedelta

#用户
class User(models.Model):
    reader_id = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    is_frozen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_reader_id(self):
        return f"R{str(uuid.uuid4().int)[:8]}"

    def save(self, *args, **kwargs):
        if not self.reader_id:
            self.reader_id = self.generate_reader_id()
        super().save(*args, **kwargs)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return not self.is_frozen  # 根据你的业务逻辑调整


class LibrarianApplication(models.Model):
    APPLICATION_STATUS = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ]

    name = models.CharField(max_length=100)
    application_reason = models.TextField()
    status = models.CharField(max_length=10, choices=APPLICATION_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)


class Librarian(models.Model):
    librarian_id = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_librarian_id(self):
        return f"L{str(uuid.uuid4().int)[:8]}"

    def save(self, *args, **kwargs):
        if not self.librarian_id:
            self.librarian_id = self.generate_librarian_id()
        super().save(*args, **kwargs)

    @property
    def is_authenticated(self):
        """始终返回True，表示用户已认证"""
        return True

    @property
    def is_anonymous(self):
        """始终返回False，表示这不是匿名用户"""
        return False

    @property
    def is_active(self):
        return True


class Book(models.Model):
    book_id = models.CharField(max_length=20, unique=True, primary_key=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    location_index = models.CharField(max_length=50)
    is_available = models.BooleanField(default=True)
    borrowed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    borrow_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_book_id(self):
        return f"B{str(uuid.uuid4().int)[:8]}"

    def save(self, *args, **kwargs):
        if not self.book_id:
            self.book_id = self.generate_book_id()
        super().save(*args, **kwargs)

    @property
    def due_date(self):
        if self.borrow_date:
            return self.borrow_date + timedelta(days=60)
        return None


class VerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return datetime.now() < self.expires_at


class WebsiteInfo(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
