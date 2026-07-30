from datetime import date

from rest_framework import serializers

from .models import RiwayatKepangkatan


class RiwayatKepangkatanListSerializer(serializers.ModelSerializer):
    """
    Serializer READ-ONLY untuk menampilkan riwayat kepangkatan pegawai.
    Dipakai untuk:
    - Staff SDM: melihat riwayat kepangkatan SEMUA pegawai (SDM-03)
    - Pegawai: melihat riwayat kepangkatan miliknya sendiri (PEG-01), lewat
      queryset yang sudah difilter di level view.

    Seluruh field bersifat read-only - perubahan data harus lewat
    RiwayatKepangkatanWriteSerializer, bukan serializer ini.
    """

    golongan_display = serializers.CharField(
        source="get_golongan_display", read_only=True
    )

    class Meta:
        model = RiwayatKepangkatan
        fields = [
            "id",
            "pegawai",
            "golongan",
            "golongan_display",
            "tmt",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RiwayatKepangkatanWriteSerializer(serializers.ModelSerializer):
    """
    Serializer WRITE untuk Staff SDM menambah/mengubah riwayat kepangkatan
    pegawai (SDM-03).

    Riwayat kepangkatan bersifat historikal/append-only, sehingga CREATE
    (menambah record riwayat baru) memang operasi normal dan diaktifkan.
    """

    class Meta:
        model = RiwayatKepangkatan
        fields = [
            "id",
            "pegawai",
            "golongan",
            "tmt",
        ]
        read_only_fields = ["id"]

    def validate_tmt(self, value):
        if value > date.today():
            raise serializers.ValidationError(
                "TMT tidak boleh lebih besar dari tanggal hari ini."
            )
        return value

    def validate(self, attrs):
        """
        Cegah input golongan yang sama persis dengan golongan aktif
        terakhir pegawai (record dengan tmt terbaru) - mencegah
        duplikasi input kepangkatan yang tidak menunjukkan perubahan.
        """
        instance = getattr(self, "instance", None)
        pegawai = attrs.get("pegawai", getattr(instance, "pegawai", None))
        golongan_baru = attrs.get("golongan", getattr(instance, "golongan", None))

        if pegawai and golongan_baru:
            qs = RiwayatKepangkatan.objects.filter(pegawai=pegawai).order_by(
                "-tmt", "-created_at"
            )
            if instance:
                qs = qs.exclude(pk=instance.pk)
            golongan_terakhir = qs.first()

            if golongan_terakhir and golongan_terakhir.golongan == golongan_baru:
                raise serializers.ValidationError(
                    {
                        "golongan": (
                            "Golongan baru tidak boleh sama dengan golongan "
                            "aktif terakhir pegawai ini."
                        )
                    }
                )

        return attrs