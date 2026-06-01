from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from taggit.managers import TaggableManager
import re
import os


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nazwa")
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Opis")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoria"
        verbose_name_plural = "Kategorie"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("blog:category_detail", kwargs={"slug": self.slug})

    def get_post_count(self):
        return self.posts.filter(status="published").count()


def post_image_path(instance, filename):
    # Zapisuje zdjęcie w folderze: media/posts/2025/01/15/nazwa_pliku
    # Każdy post ma swój katalog według daty — porządek w plikach
    ext = filename.rsplit(".", 1)[-1].lower()
    safe_name = slugify(instance.title or "post")[:40]
    return f"posts/{instance.publish_date.strftime('%Y/%m/%d')}/{safe_name}.{ext}"


class Post(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Szkic"),
        (STATUS_PUBLISHED, "Opublikowany"),
    ]

    title = models.CharField(max_length=250, verbose_name="Tytuł")
    slug = models.SlugField(max_length=250, unique_for_date="publish_date", verbose_name="Slug")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts", verbose_name="Autor"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="posts", verbose_name="Kategoria"
    )
    body = models.TextField(verbose_name="Treść")
    excerpt = models.TextField(max_length=500, blank=True, verbose_name="Zajawka")
    image = models.ImageField(
        upload_to=post_image_path,
        null=True,
        blank=True,
        verbose_name="Zdjęcie główne",
        help_text="Opcjonalne zdjęcie wyróżniające wpis (JPG, PNG, WEBP)"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT, verbose_name="Status"
    )
    publish_date = models.DateTimeField(default=timezone.now, verbose_name="Data publikacji")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        User, related_name="liked_posts", blank=True, verbose_name="Polubienia"
    )
    tags = TaggableManager(blank=True, verbose_name="Tagi")

    class Meta:
        verbose_name = "Wpis"
        verbose_name_plural = "Wpisy"
        ordering = ["-publish_date"]
        indexes = [
            models.Index(fields=["-publish_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.excerpt:
            clean_body = re.sub(r"<[^>]+>", "", self.body)
            self.excerpt = clean_body[:300] + ("..." if len(clean_body) > 300 else "")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "blog:post_detail",
            kwargs={
                "year": self.publish_date.year,
                "month": self.publish_date.month,
                "day": self.publish_date.day,
                "slug": self.slug,
            },
        )

    def get_like_count(self):
        return self.likes.count()

    def is_liked_by(self, user):
        if user.is_authenticated:
            return self.likes.filter(pk=user.pk).exists()
        return False

    def get_comment_count(self):
        return self.comments.filter(active=True).count()

    def get_similar_posts(self, count=4):
        post_tags_ids = self.tags.values_list("id", flat=True)
        similar_posts = (
            Post.objects.filter(status=Post.STATUS_PUBLISHED)
            .filter(tags__in=post_tags_ids)
            .exclude(id=self.id)
        )
        from django.db.models import Count
        similar_posts = (
            similar_posts.annotate(same_tags=Count("tags"))
            .order_by("-same_tags", "-publish_date")[:count]
        )
        return similar_posts


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Wpis"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments", verbose_name="Autor"
    )
    body = models.TextField(verbose_name="Treść komentarza")
    active = models.BooleanField(default=True, verbose_name="Aktywny")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Komentarz"
        verbose_name_plural = "Komentarze"
        ordering = ["created_at"]

    def __str__(self):
        return f"Komentarz od {self.author.username} do '{self.post.title}'"


class Profile(models.Model):
    # Dostępne motywy kolorystyczne
    THEME_CHOICES = [
        ("orange", "Klasyczny pomarańczowy"),
        ("blue", "Oceaniczny niebieski"),
        ("green", "Leśna zieleń"),
        ("purple", "Królewska purpura"),
        ("red", "Płomienna czerwień"),
        ("teal", "Morski turkus"),
        ("dark", "Ciemny"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name="Użytkownik"
    )
    bio = models.TextField(blank=True, verbose_name="O mnie")
    location = models.CharField(max_length=100, blank=True, verbose_name="Lokalizacja")
    website = models.URLField(blank=True, verbose_name="Strona WWW")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data urodzenia")
    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default="orange",
        verbose_name="Motyw kolorystyczny",
        help_text="Twój osobisty motyw kolorystyczny interfejsu"
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name="Zweryfikowany",
        help_text="Znaczek weryfikacji nadawany przez administratora"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profile"

    def __str__(self):
        return f"Profil użytkownika {self.user.username}"

    def get_absolute_url(self):
        return reverse("blog:profile_detail", kwargs={"username": self.user.username})

    def get_post_count(self):
        return Post.objects.filter(author=self.user, status=Post.STATUS_PUBLISHED).count()

    def get_comment_count(self):
        return Comment.objects.filter(author=self.user).count()

    def get_theme_css_class(self):
        return f"theme-{self.theme}"