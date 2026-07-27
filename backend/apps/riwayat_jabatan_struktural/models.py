import uuid
from django.core.exceptions import ValidationError
from django.db import models

from apps.pegawai.models import Pegawai


class RiwayatJabatanStruktural(models.Model):
    """
    Riwayat jabatan struktural pegawai (contoh: Kaprodi, Dekan, Kepala Biro).
    Bersifat historikal (append-only). Berbeda dari riwayat lain karena
    punya field `selesai` yang menandai kapan jabatan tersebut berakhir -
    nullable karena jabatan bisa saja masih aktif hingga saat ini.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    pegawai = models.ForeignKey(
        Pegawai,
        on_delete=models.CASCADE,
        related_name="riwayat_jabatan_struktural",
    )
    jabatan = models.ForeignKey(
        "organisasi.JabatanStrukturalMaster",
        on_delete=models.PROTECT,
        related_name="riwayat_jabatan_struktural",
    )
    tmt = models.DateField(
        help_text="Tanggal Mulai Tugas / tanggal mulai menjabat.",
    )
    selesai = models.DateField(
        null=True,
        blank=True,
        help_text="Tanggal berakhir menjabat. Kosongkan jika masih menjabat.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Riwayat Jabatan Struktural"
        verbose_name_plural = "Riwayat Jabatan Struktural"
        ordering = ["pegawai", "tmt"]

    def clean(self):
        if self.selesai and self.tmt and self.selesai < self.tmt:
            raise ValidationError(
                "Tanggal selesai tidak boleh lebih awal dari tanggal mulai tugas (tmt)."
            )

    @property
    def masih_menjabat(self):
        return self.selesai is None

    def __str__(self):
        status = "aktif" if self.masih_menjabat else f"selesai {self.selesai}"
        return f"{self.pegawai.nama_lengkap} - {self.jabatan} ({status})"