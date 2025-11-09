from django.contrib import admin
from .models import User, Librarian, Book, VerificationCode, WebsiteInfo, LibrarianApplication

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['reader_id', 'name', 'email', 'is_frozen', 'created_at']
    search_fields = ['reader_id', 'name', 'email']

@admin.register(Librarian)
class LibrarianAdmin(admin.ModelAdmin):
    list_display = ['librarian_id', 'name', 'email', 'created_at']
    search_fields = ['librarian_id', 'name', 'email']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['book_id', 'title', 'author', 'is_available', 'borrowed_by', 'borrow_date']
    search_fields = ['book_id', 'title', 'author']

@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ['email', 'code', 'created_at', 'expires_at']

@admin.register(WebsiteInfo)
class WebsiteInfoAdmin(admin.ModelAdmin):
    list_display = ['title', 'updated_at']

@admin.register(LibrarianApplication)
class LibrarianApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_at']
    list_filter = ['status']