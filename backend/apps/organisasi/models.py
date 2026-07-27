import uuid
from django.db import models


class JabatanStrukturalMaster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_jabatan = models.CharField(max_length=100, unique=True)
    level = models.PositiveSmallIntegerField(
        help_text="Urutan hierarki, contoh: 1=Rektor, 2=Dekan, 3=Kaprodi.",
    )
    aktif = models.BooleanField(
        default=True,
        help_text="Nonaktifkan jika jabatan ini sudah tidak berlaku, jangan dihapus.",
    )

    class Meta:
        verbose_name = "Jabatan Struktural (Master)"
        ordering = ["level", "nama_jabatan"]

    def __str__(self):
        return self.nama_jabatan