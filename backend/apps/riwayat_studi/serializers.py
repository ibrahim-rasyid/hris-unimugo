from datetime import date

from rest_framework import serializers

from .models import RiwayatStudi


class RiwayatStudiListSerializer(serializers.ModelSerializer):
    """
    Serializer READ-ONLY untuk menampilkan riwayat studi pegawai.
    Dipakai untuk:
    - Staff SDM: melihat riwayat studi SEMUA pegawai (SDM-02)
    - Pegawai: melihat riwayat studi miliknya sendiri (PEG-01), lewat
      queryset yang sudah difilter di level view.

    Seluruh field bersifat read-only - perubahan data harus lewat
    RiwayatStudiWriteSerializer, bukan serializer ini.
    """

    jenjang_display = serializers.CharField(
        source="get_jenjang_display", read_only=True
    )

    class Meta:
        model = RiwayatStudi
        fields = [
            "id",
            "pegawai",
            "jenjang",
            "jenjang_display",
            "institusi",
            "gelar",
            "tahun_lulus",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RiwayatStudiWriteSerializer(serializers.ModelSerializer):
    """
    Serializer WRITE untuk Staff SDM menambah/mengubah riwayat studi
    pegawai (SDM-02).

    Berbeda dari PegawaiUpdateSerializer: riwayat studi bersifat
    historikal/append-only, sehingga CREATE (menambah record riwayat
    baru) memang operasi normal dan diaktifkan - bukan operasi
    berisiko seperti membuat Pegawai baru.
    """

    class Meta:
        model = RiwayatStudi
        fields = [
            "id",
            "pegawai",
            "jenjang",
            "institusi",
            "gelar",
            "tahun_lulus",
        ]
        read_only_fields = ["id"]

    def validate_tahun_lulus(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                "Tahun lulus tidak boleh lebih besar dari tanggal hari ini."
            )
        return value