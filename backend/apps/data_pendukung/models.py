import uuid
from django.db import models

from apps.pegawai.models import Pegawai


class DataPendukung(models.Model):
    """
    Data pendukung pegawai yang bersifat self-service.
    Relasi 1-1 ke Pegawai. Ini SATU-SATUNYA tabel yang boleh
    diubah langsung oleh role Pegawai untuk dirinya sendiri -
    berbeda dari tabel lain yang hanya bisa diubah Staff SDM.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    pegawai = models.OneToOneField(
        Pegawai,
        on_delete=models.CASCADE,
        related_name="data_pendukung",
    )
    alamat = models.TextField(
        blank=True,
        help_text="Alamat domisili saat ini.",
    )
    kontak_darurat_nama = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nama kontak darurat (next-of-kin).",
    )
    kontak_darurat_hubungan = models.CharField(
        max_length=50,
        blank=True,
        help_text="Contoh: Suami, Istri, Orang tua, Saudara kandung.",
    )
    kontak_darurat_no_hp = models.CharField(
        max_length=20,
        blank=True,
    )
    email_kedua = models.EmailField(
        blank=True,
        help_text="Email alternatif di luar email institusi.",
    )
    no_hp = models.CharField(
        max_length=20,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Data Pendukung"
        verbose_name_plural = "Data Pendukung"

    def __str__(self):
        return f"Data pendukung - {self.pegawai.nama_lengkap}"