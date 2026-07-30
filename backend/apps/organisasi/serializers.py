from rest_framework import serializers

from .models import JabatanStrukturalMaster


class JabatanStrukturalMasterSerializer(serializers.ModelSerializer):
    """
    Serializer untuk data master jabatan struktural (ADM-05).
    Data ini bersifat konfigurasi/referensi (bukan historikal), sehingga
    semua field writable kecuali id.
    """

    class Meta:
        model = JabatanStrukturalMaster
        fields = [
            "id",
            "nama_jabatan",
            "level",
            "aktif",
        ]
        read_only_fields = ["id"]
