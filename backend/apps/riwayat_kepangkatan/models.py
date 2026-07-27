import uuid
from django.db import models

from apps.pegawai.models import Pegawai


class RiwayatKepangkatan(models.Model):
    """
    Riwayat kepangkatan/golongan pegawai.
    Bersifat historikal (append-only) - setiap kenaikan pangkat
    dicatat sebagai record baru, bukan menimpa record lama.
    """

    class Golongan(models.TextChoices):
        II_A = "II/a", "II/a"
        II_B = "II/b", "II/b"
        II_C = "II/c", "II/c"
        II_D = "II/d", "II/d"
        III_A = "III/a", "III/a"
        III_B = "III/b", "III/b"
        III_C = "III/c", "III/c"
        III_D = "III/d", "III/d"
        IV_A = "IV/a", "IV/a"
        IV_B = "IV/b", "IV/b"
        IV_C = "IV/c", "IV/c"
        IV_D = "IV/d", "IV/d"
        IV_E = "IV/e", "IV/e"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    pegawai = models.ForeignKey(
        Pegawai,
        on_delete=models.CASCADE,
        related_name="riwayat_kepangkatan",
    )
    golongan = models.CharField(
        max_length=6,
        choices=Golongan.choices,
    )
    tmt = models.DateField(
        help_text="Tanggal Mulai Tugas / tanggal berlaku golongan ini.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Riwayat Kepangkatan"
        verbose_name_plural = "Riwayat Kepangkatan"
        ordering = ["pegawai", "tmt"]

    def __str__(self):
        return f"{self.pegawai.nama_lengkap} - {self.golongan} (TMT {self.tmt})"