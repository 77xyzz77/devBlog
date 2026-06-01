from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Comment, Profile, Post, Category


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Napisz swój komentarz...",
                "class": "form-control",
            }),
        }
        labels = {"body": ""}


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "placeholder": "Twój adres email",
            "class": "form-control",
        }),
        label="Email",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={
                "placeholder": "Nazwa użytkownika",
                "class": "form-control",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({
            "placeholder": "Hasło (min. 8 znaków)",
            "class": "form-control",
        })
        self.fields["password2"].widget.attrs.update({
            "placeholder": "Powtórz hasło",
            "class": "form-control",
        })
        for field_name in self.fields:
            self.fields[field_name].help_text = None

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Ten adres email jest już zajęty.")
        return email


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        label="Email",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
        }
        labels = {
            "first_name": "Imię",
            "last_name": "Nazwisko",
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ten adres email jest już zajęty.")
        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "location", "website", "birth_date", "theme"]
        widgets = {
            "bio": forms.Textarea(attrs={
                "rows": 4,
                "class": "form-control",
                "placeholder": "Napisz coś o sobie...",
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "np. Warszawa, Polska",
            }),
            "website": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://twoja-strona.pl",
            }),
            "birth_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "theme": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "bio": "O mnie",
            "location": "Lokalizacja",
            "website": "Strona WWW",
            "birth_date": "Data urodzenia",
            "theme": "Motyw kolorystyczny",
        }


class PostForm(forms.ModelForm):
    """
    Formularz tworzenia i edycji wpisu.
    Używamy ModelForm — Django generuje pola z modelu Post.
    Użytkownik może wybrać status: szkic lub opublikowany.
    """
    tags_input = forms.CharField(
        required=False,
        label="Tagi",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "python, django, webdev (oddziel przecinkami)",
        }),
        help_text="Wpisz tagi oddzielone przecinkami",
    )

    class Meta:
        model = Post
        fields = ["title", "category", "body", "excerpt", "image", "status"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Tytuł wpisu...",
            }),
            "category": forms.Select(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 16,
                "placeholder": "Treść wpisu...",
            }),
            "excerpt": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Krótki opis (opcjonalnie — zostanie wygenerowany automatycznie)...",
            }),
            "image": forms.FileInput(attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/png,image/webp",
            }),
            "status": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "title": "Tytuł",
            "category": "Kategoria",
            "body": "Treść",
            "excerpt": "Zajawka",
            "image": "Zdjęcie główne",
            "status": "Status",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].empty_label = "— Bez kategorii —"
        self.fields["category"].required = False
        # Jeśli edytujemy istniejący post, wypełniamy pole tagów
        if self.instance and self.instance.pk:
            existing_tags = self.instance.tags.values_list("name", flat=True)
            self.fields["tags_input"].initial = ", ".join(existing_tags)

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and hasattr(image, "size"):
            # Limit rozmiaru pliku: 5 MB
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Zdjęcie nie może być większe niż 5 MB.")
            # Sprawdzamy rozszerzenie
            ext = image.name.rsplit(".", 1)[-1].lower()
            if ext not in ["jpg", "jpeg", "png", "webp"]:
                raise forms.ValidationError("Dozwolone formaty: JPG, PNG, WEBP.")
        return image

    def save(self, commit=True):
        post = super().save(commit=False)
        if commit:
            post.save()
            # Obsługa tagów — django-taggit ma własną metodę set()
            tags_value = self.cleaned_data.get("tags_input", "")
            if tags_value.strip():
                tag_list = [t.strip() for t in tags_value.split(",") if t.strip()]
                post.tags.set(*tag_list)
            else:
                post.tags.clear()
        return post