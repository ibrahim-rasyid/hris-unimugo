import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.manager import UserManager


class Role(models.Model):
    class NamaRole(models.TextChoices):
        ADMIN = "admin", "Admin"
        STAFF_SDM = "staff_sdm", "Staff SDM"
        DOSEN = "dosen", "Dosen"
        TENDIK = "tendik", "Tendik"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_role = models.CharField(
        max_length=20,
        choices=NamaRole.choices,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nama_role"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self) -> str:
        return self.get_nama_role_display()


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="users",
    )
    objects = UserManager()  # Custom manager
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["username"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.username