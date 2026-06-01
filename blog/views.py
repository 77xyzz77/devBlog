from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from .models import Post, Category, Comment, Profile
from .forms import (
    CommentForm,
    UserRegisterForm,
    UserUpdateForm,
    ProfileUpdateForm,
    PostForm,
)


def home(request):
    posts_list = Post.objects.filter(
        status=Post.STATUS_PUBLISHED
    ).select_related(
        "author", "author__profile", "category"
    ).prefetch_related("tags", "likes")

    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get("strona", 1)
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.annotate(
        post_count=Count("posts", filter=Q(posts__status=Post.STATUS_PUBLISHED))
    ).filter(post_count__gt=0)

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "page_title": "Strona główna",
    }
    return render(request, "blog/home.html", context)


def post_list(request):
    posts_list = Post.objects.filter(
        status=Post.STATUS_PUBLISHED
    ).select_related("author", "author__profile", "category").prefetch_related("tags", "likes")

    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get("strona", 1)
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.annotate(
        post_count=Count("posts", filter=Q(posts__status=Post.STATUS_PUBLISHED))
    ).filter(post_count__gt=0)

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "page_title": "Wszystkie wpisy",
    }
    return render(request, "blog/home.html", context)


def post_detail(request, year, month, day, slug):
    post = get_object_or_404(
        Post,
        status=Post.STATUS_PUBLISHED,
        publish_date__year=year,
        publish_date__month=month,
        publish_date__day=day,
        slug=slug,
    )

    comments = post.comments.filter(active=True).select_related("author", "author__profile")
    similar_posts = post.get_similar_posts()
    comment_form = CommentForm()

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Musisz być zalogowany żeby dodać komentarz.")
            return redirect("blog:login")
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

            # POWIADOMIENIE EMAIL do autora wpisu
            # Wysyłamy tylko jeśli komentujący to nie autor wpisu
            # i autor ma adres email
            if (
                request.user != post.author
                and post.author.email
            ):
                try:
                    send_mail(
                        subject=f"Nowy komentarz do Twojego wpisu: {post.title}",
                        message=(
                            f"Cześć {post.author.username},\n\n"
                            f"{request.user.username} skomentował Twój wpis "
                            f"„{post.title}”:\n\n"
                            f"{comment.body}\n\n"
                            f"Zobacz wpis: "
                            f"http://127.0.0.1:8000{post.get_absolute_url()}\n\n"
                            f"Pozdrawiamy,\nZespół DevBlog"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[post.author.email],
                        fail_silently=True,
                        # fail_silently=True: błąd emaila nie psuje działania strony
                    )
                except Exception:
                    pass

            messages.success(request, "Komentarz został dodany!")
            return redirect(post.get_absolute_url() + "#komentarze")

    context = {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
        "similar_posts": similar_posts,
        "is_liked": post.is_liked_by(request.user),
        "page_title": post.title,
    }
    return render(request, "blog/post_detail.html", context)


@login_required
def post_like(request, pk):
    if request.method == "POST":
        post = get_object_or_404(Post, pk=pk, status=Post.STATUS_PUBLISHED)
        if post.is_liked_by(request.user):
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        return JsonResponse({"liked": liked, "count": post.get_like_count()})
    return JsonResponse({"error": "Niedozwolona metoda"}, status=405)


@login_required
def post_create(request):
    """
    Tworzenie nowego wpisu.
    Tylko zalogowani użytkownicy mogą tworzyć wpisy.
    """
    if request.method == "POST":
        # request.FILES zawiera przesłane pliki — jak $_FILES w PHP
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            # Musimy wywołać save_m2m() po ręcznym save() z commit=False
            # bo tagi to pole ManyToMany — zapisywane oddzielnie
            form.save_m2m()
            # Ale tagi obsługujemy w metodzie save() formularza, więc wywołujemy ją jeszcze raz
            tags_value = form.cleaned_data.get("tags_input", "")
            if tags_value.strip():
                tag_list = [t.strip() for t in tags_value.split(",") if t.strip()]
                post.tags.set(tag_list)
            else:
                post.tags.clear()

            if post.status == Post.STATUS_PUBLISHED:
                messages.success(request, "Wpis został opublikowany!")
                return redirect(post.get_absolute_url())
            else:
                messages.success(request, "Wpis został zapisany jako szkic.")
                return redirect("blog:post_edit", pk=post.pk)
    else:
        form = PostForm()

    return render(request, "blog/post_form.html", {
        "form": form,
        "page_title": "Nowy wpis",
        "action": "create",
    })


@login_required
def post_edit(request, pk):
    """
    Edycja wpisu — tylko autor lub administrator.
    """
    post = get_object_or_404(Post, pk=pk)

    # Sprawdzamy czy zalogowany użytkownik jest autorem lub adminem
    # W PHP: if ($_SESSION["user_id"] != $post["author_id"] && !$_SESSION["is_admin"])
    if request.user != post.author and not request.user.is_staff:
        messages.error(request, "Nie masz uprawnień do edycji tego wpisu.")
        return redirect(post.get_absolute_url())

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            updated_post = form.save(commit=False)
            updated_post.save()
            
            tags_value = form.cleaned_data.get("tags_input", "")
            if tags_value.strip():
                tag_list = [t.strip() for t in tags_value.split(",") if t.strip()]
                post.tags.set(tag_list)
            else:
                post.tags.clear()
    else:
        form = PostForm(instance=post)

    return render(request, "blog/post_form.html", {
        "form": form,
        "post": post,
        "page_title": f"Edytuj: {post.title}",
        "action": "edit",
    })


@login_required
def post_delete(request, pk):
    """
    Usuwanie wpisu — tylko autor lub administrator, tylko przez POST.
    """
    post = get_object_or_404(Post, pk=pk)
    if request.user != post.author and not request.user.is_staff:
        messages.error(request, "Nie masz uprawnień do usunięcia tego wpisu.")
        return redirect(post.get_absolute_url())

    if request.method == "POST":
        post.delete()
        messages.success(request, "Wpis został usunięty.")
        return redirect("blog:home")

    return render(request, "blog/post_confirm_delete.html", {
        "post": post,
        "page_title": f"Usuń wpis: {post.title}",
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts_list = Post.objects.filter(
        category=category, status=Post.STATUS_PUBLISHED
    ).select_related("author", "author__profile").prefetch_related("tags", "likes")

    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get("strona", 1)
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.annotate(
        post_count=Count("posts", filter=Q(posts__status=Post.STATUS_PUBLISHED))
    ).filter(post_count__gt=0)

    context = {
        "category": category,
        "page_obj": page_obj,
        "categories": categories,
        "page_title": f"Kategoria: {category.name}",
    }
    return render(request, "blog/category.html", context)


def search(request):
    query = request.GET.get("q", "").strip()
    results = Post.objects.none()

    if query and len(query) >= 2:
        results = Post.objects.filter(
            status=Post.STATUS_PUBLISHED
        ).filter(
            Q(title__icontains=query) |
            Q(body__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(tags__name__icontains=query)
        ).select_related(
            "author", "author__profile", "category"
        ).prefetch_related("tags", "likes").distinct()

    paginator = Paginator(results, 10)
    page_number = request.GET.get("strona", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "query": query,
        "page_obj": page_obj,
        "result_count": results.count() if query else 0,
        "page_title": f"Wyniki: {query}" if query else "Wyszukiwarka",
    }
    return render(request, "blog/search.html", context)


def profile_detail(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(
        author=profile_user, status=Post.STATUS_PUBLISHED
    ).select_related("category").prefetch_related("tags", "likes")

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("strona", 1)
    page_obj = paginator.get_page(page_number)

    context = {
        "profile_user": profile_user,
        "page_obj": page_obj,
        "page_title": f"Profil: {profile_user.username}",
    }
    return render(request, "blog/profile.html", context)


@login_required
def profile_edit(request):
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profil został zaktualizowany!")
            return redirect("blog:profile_detail", username=request.user.username)
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        "user_form": user_form,
        "profile_form": profile_form,
        "page_title": "Edytuj profil",
    }
    return render(request, "blog/profile_edit.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("blog:home")
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Witaj, {user.username}! Konto zostało utworzone.")
            return redirect("blog:home")
    else:
        form = UserRegisterForm()
    return render(request, "blog/register.html", {"form": form, "page_title": "Rejestracja"})