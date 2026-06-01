from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


# @receiver to dekorator — mówi Django: "gdy User zostanie zapisany, wywołaj tę funkcję"
# post_save = sygnał wysyłany PO zapisie modelu
# sender=User = interesują nas tylko sygnały od modelu User

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatycznie tworzy profil gdy rejestruje się nowy użytkownik.
    'created' to True tylko przy pierwszym zapisie (INSERT), False przy UPDATE.
    W PHP musiałeś pamiętać żeby po INSERT INTO users zrobić INSERT INTO profiles.
    Tutaj Django robi to za Ciebie automatycznie.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Zapisuje profil gdy zapisujemy użytkownika.
    Zabezpieczenie — jeśli profil istnieje, aktualizuje go.
    Jeśli z jakiegoś powodu nie istnieje, tworzy go.
    """
    if hasattr(instance, "profile"):
        instance.profile.save()
    else:
        Profile.objects.create(user=instance)