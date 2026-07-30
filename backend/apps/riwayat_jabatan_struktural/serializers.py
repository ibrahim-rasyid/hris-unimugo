from rest_framework import serializers

from apps.organisasi.models import JabatanStrukturalMaster
from apps.organisasi.serializers import JabatanStrukturalMasterSerializer

from .models import RiwayatJabatanStruktural


class RiwayatJabatanStrukturalListSerializer(serializers.ModelSerializer):
    """
    Serializer READ-ONLY untuk menampilkan riwayat jabatan struktural
    pegawai. Dipakai untuk:
    - Staff SDM: melihat riwayat jabatan struktural SEMUA pegawai (SDM-05)
    - Pegawai: melihat riwayat jabatan struktural miliknya sendiri (PEG-01),
      lewat queryset yang sudah difilter di level view.

    Field `jabatan` di-nested (bukan cuma ID) supaya nama & level jabatan
    langsung tersedia tanpa request tambahan ke endpoint master.

    Seluruh field bersifat read-only - perubahan data harus lewat
    RiwayatJabatanStrukturalWriteSerializer, bukan serializer ini.
    """

    jabatan = JabatanStrukturalMasterSerializer(read_only=True)
    masih_menjabat = serializers.BooleanField(read_only=True)

    class Meta:
        model = RiwayatJabatanStruktural
        fields = [
            "id",
            "pegawai",
            "jabatan",
            "tmt",
            "selesai",
            "masih_menjabat",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RiwayatJabatanStrukturalWriteSerializer(serializers.ModelSerializer):
    """
    Serializer WRITE untuk Staff SDM menambah/mengubah riwayat jabatan
    struktural pegawai (SDM-05).

    Riwayat jabatan struktural bersifat historikal/append-only, sehingga
    CREATE (menambah record riwayat baru) memang operasi normal dan
    diaktifkan.
    """

    class Meta:
        model = RiwayatJabatanStruktural
        fields = [
            "id",
            "pegawai",
            "jabatan",
            "tmt",
            "selesai",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        """
        Replikasi logika clean() model RiwayatJabatanStruktural, karena
        clean() model TIDAK otomatis jalan saat save() dari serializer:
        1. Jika selesai diisi, selesai tidak boleh lebih awal dari tmt.
        2. Jabatan yang dipilih harus JabatanStrukturalMaster dengan
           aktif=True - tidak boleh assign jabatan yang sudah dinonaktifkan.
        """
        instance = getattr(self, "instance", None)
        tmt = attrs.get("tmt", getattr(instance, "tmt", None))
        selesai = attrs.get("selesai", getattr(instance, "selesai", None))
        jabatan = attrs.get("jabatan", getattr(instance, "jabatan", None))

        if selesai and tmt and selesai < tmt:
            raise serializers.ValidationError(
                {
                    "selesai": (
                        "Tanggal selesai tidak boleh lebih awal dari "
                        "tanggal mulai tugas (tmt)."
                    )
                }
            )

        if jabatan and not jabatan.aktif:
            raise serializers.ValidationError(
                {
                    "jabatan": (
                        "Jabatan struktural ini sudah tidak aktif dan "
                        "tidak dapat digunakan untuk riwayat baru."
                    )
                }
            )

        return attrs
