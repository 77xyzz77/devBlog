from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Post, Comment, Profile


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "get_post_count", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    # prepopulated_fields: gdy piszesz nazwę, slug wypełnia się automatycznie w adminie
    search_fields = ["name"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "status", "publish_date", "get_like_count", "get_comment_count"]
    list_filter = ["status", "category", "publish_date", "author"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["author"]
    date_hierarchy = "publish_date"
    ordering = ["-publish_date"]
    list_editable = ["status"]
    # list_editable: możesz zmieniać status bezpośrednio na liście bez wchodzenia w post


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author", "post", "created_at", "active"]
    list_filter = ["active", "created_at"]
    search_fields = ["author__username", "body"]
    list_editable = ["active"]
    # author__username: dwukrotny podkreślnik = przejście po relacji
    # W PHP: JOIN users ON comments.author_id = users.id WHERE users.username LIKE...


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "location", "website", "created_at"]
    search_fields = ["user__username", "bio", "location"]
    raw_id_fields = ["user"]