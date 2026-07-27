import uuid
from django.db import models

from apps.pegawai.models import Pegawai


class RiwayatStudi(models.Model):
    """
    Riwayat pendidikan dan gelar akademik pegawai.
    Bersifat historikal (append-only) - satu pegawai bisa punya
    banyak record riwayat studi (S1, S2, S3, dst).
    """

    class Jenjang(models.TextChoices):
        S1 = "S1", "Sarjana (S1)"
        S2 = "S2", "Magister (S2)"
        S3 = "S3", "Doktor (S3)"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    pegawai = models.ForeignKey(
        Pegawai,
        on_delete=models.CASCADE,
        related_name="riwayat_studi",
    )
    jenjang = models.CharField(
        max_length=2,
        choices=Jenjang.choices,
    )
    institusi = models.CharField(
        max_length=150,
        help_text="Nama perguruan tinggi tempat menempuh studi.",
    )
    gelar = models.CharField(
        max_length=50,
        help_text="Contoh: S.Kom, M.T, Dr.",
    )
    tahun_lulus = models.DateField(
        help_text="Tanggal/tahun kelulusan.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Riwayat Studi"
        verbose_name_plural = "Riwayat Studi"
        ordering = ["pegawai", "tahun_lulus"]

    def __str__(self):
        return f"{self.pegawai.nama_lengkap} - {self.jenjang} ({self.institusi})"