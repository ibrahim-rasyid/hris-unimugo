import uuid
from django.conf import settings
from django.db import models


class Pegawai(models.Model):
    """
    Data induk pegawai (dosen dan tenaga kependidikan).
    Relasi 1-1 ke User (akun login).
    Semua riwayat (studi, kepangkatan, jabatan) mereferensikan model ini.
    """

    class JenisPegawai(models.TextChoices):
        DOSEN = "dosen", "Dosen"
        TENDIK = "tendik", "Tenaga Kependidikan"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pegawai",
        help_text="Akun login yang terhubung dengan data pegawai ini.",
    )
    nip_nidn = models.CharField(
        max_length=30,
        unique=True,
        help_text="NIP untuk tendik, NIDN untuk dosen.",
    )
    nama_lengkap = models.CharField(max_length=150)
    jenis_pegawai = models.CharField(
        max_length=10,
        choices=JenisPegawai.choices,
    )
    unit_kerja = models.CharField(
        max_length=100,
        help_text="Contoh: Fakultas Teknik, Biro Administrasi Umum.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pegawai"
        verbose_name_plural = "Pegawai"
        ordering = ["nama_lengkap"]

    def __str__(self):
        return f"{self.nama_lengkap} ({self.nip_nidn})"