from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        BUYER = "buyer", "Buyer"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.BUYER,
        help_text="User role determines dashboard access",
    )

# Create your models here.
