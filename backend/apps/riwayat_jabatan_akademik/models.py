import uuid
from django.core.exceptions import ValidationError
from django.db import models

from apps.pegawai.models import Pegawai


class RiwayatJabatanAkademik(models.Model):
    """
    Riwayat jabatan akademik pegawai (khusus dosen).
    Bersifat historikal (append-only) - setiap kenaikan jabatan akademik
    dicatat sebagai record baru, bukan menimpa record lama.
    """

    class Jabatan(models.TextChoices):
        ASISTEN_AHLI = "asisten_ahli", "Asisten Ahli"
        LEKTOR = "lektor", "Lektor"
        LEKTOR_KEPALA = "lektor_kepala", "Lektor Kepala"
        GURU_BESAR = "guru_besar", "Guru Besar"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    pegawai = models.ForeignKey(
        Pegawai,
        on_delete=models.CASCADE,
        related_name="riwayat_jabatan_akademik",
    )
    jabatan = models.CharField(
        max_length=20,
        choices=Jabatan.choices,
    )
    tmt = models.DateField(
        help_text="Tanggal Mulai Tugas / tanggal berlaku jabatan akademik ini.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Riwayat Jabatan Akademik"
        verbose_name_plural = "Riwayat Jabatan Akademik"
        ordering = ["pegawai", "tmt"]

    def clean(self):
        # Jabatan akademik khusus untuk dosen, bukan tendik.
        if self.pegawai_id and self.pegawai.jenis_pegawai != Pegawai.JenisPegawai.DOSEN:
            raise ValidationError(
                "Jabatan akademik hanya berlaku untuk pegawai jenis Dosen."
            )

    def __str__(self):
        return f"{self.pegawai.nama_lengkap} - {self.get_jabatan_display()} (TMT {self.tmt})"