from datetime import date

from rest_framework import serializers

from apps.pegawai.models import Pegawai

from .models import RiwayatJabatanAkademik


class RiwayatJabatanAkademikListSerializer(serializers.ModelSerializer):
    """
    Serializer READ-ONLY untuk menampilkan riwayat jabatan akademik pegawai.
    Dipakai untuk:
    - Staff SDM: melihat riwayat jabatan akademik SEMUA pegawai (SDM-04)
    - Pegawai: melihat riwayat jabatan akademik miliknya sendiri (PEG-01),
      lewat queryset yang sudah difilter di level view.

    Seluruh field bersifat read-only - perubahan data harus lewat
    RiwayatJabatanAkademikWriteSerializer, bukan serializer ini.
    """

    jabatan_display = serializers.CharField(
        source="get_jabatan_display", read_only=True
    )

    class Meta:
        model = RiwayatJabatanAkademik
        fields = [
            "id",
            "pegawai",
            "jabatan",
            "jabatan_display",
            "tmt",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RiwayatJabatanAkademikWriteSerializer(serializers.ModelSerializer):
    """
    Serializer WRITE untuk Staff SDM menambah/mengubah riwayat jabatan
    akademik pegawai (SDM-04).

    Riwayat jabatan akademik bersifat historikal/append-only, sehingga
    CREATE (menambah record riwayat baru) memang operasi normal dan
    diaktifkan.
    """

    class Meta:
        model = RiwayatJabatanAkademik
        fields = [
            "id",
            "pegawai",
            "jabatan",
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
        Replikasi logika clean() model RiwayatJabatanAkademik, karena
        clean() model TIDAK otomatis jalan saat save() dari serializer:
        1. Jabatan akademik hanya berlaku untuk pegawai jenis Dosen.
        2. Cegah input jabatan yang sama persis dengan jabatan aktif
           terakhir pegawai (record dengan tmt terbaru) - mencegah
           duplikasi input jabatan yang tidak menunjukkan perubahan.
        """
        instance = getattr(self, "instance", None)
        pegawai = attrs.get("pegawai", getattr(instance, "pegawai", None))
        jabatan_baru = attrs.get("jabatan", getattr(instance, "jabatan", None))

        if pegawai and pegawai.jenis_pegawai != Pegawai.JenisPegawai.DOSEN:
            raise serializers.ValidationError(
                {
                    "pegawai": (
                        "Jabatan akademik hanya berlaku untuk pegawai jenis Dosen."
                    )
                }
            )

        if pegawai and jabatan_baru:
            qs = RiwayatJabatanAkademik.objects.filter(pegawai=pegawai).order_by(
                "-tmt", "-created_at"
            )
            if instance:
                qs = qs.exclude(pk=instance.pk)
            jabatan_terakhir = qs.first()

            if jabatan_terakhir and jabatan_terakhir.jabatan == jabatan_baru:
                raise serializers.ValidationError(
                    {
                        "jabatan": (
                            "Jabatan baru tidak boleh sama dengan jabatan "
                            "aktif terakhir pegawai ini."
                        )
                    }
                )

        return attrs
