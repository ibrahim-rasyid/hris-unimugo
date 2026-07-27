from rest_framework import serializers

from apps.accounts.serializers import UserMiniSerializer

from .models import Pegawai


class PegawaiListSerializer(serializers.ModelSerializer):
    """
    Serializer READ-ONLY untuk menampilkan data pegawai.
    Dipakai untuk:
    - Staff SDM: melihat daftar/detail SEMUA pegawai (SDM-01)
    - Pegawai: melihat data pribadinya sendiri (PEG-01), lewat queryset
      yang sudah difilter di level view - serializer ini sendiri
      tidak membedakan siapa yang mengakses.

    Seluruh field bersifat read-only - perubahan data harus lewat
    PegawaiUpdateSerializer, bukan serializer ini.
    """

    user = UserMiniSerializer(read_only=True)
    jenis_pegawai_display = serializers.CharField(
        source="get_jenis_pegawai_display", read_only=True
    )

    class Meta:
        model = Pegawai
        fields = [
            "id",
            "user",
            "nip_nidn",
            "nama_lengkap",
            "jenis_pegawai",
            "jenis_pegawai_display",
            "unit_kerja",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PegawaiUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer WRITE untuk Staff SDM meng-update data induk pegawai (SDM-01).

    Field `user` SENGAJA tidak disertakan sebagai writable - keterkaitan
    akun (User) ke data pegawai hanya boleh dilakukan lewat proses terpisah
    (mis. saat pembuatan akun pegawai baru oleh Admin/Staff SDM), bukan
    lewat endpoint update data pegawai biasa. Ini mencegah Staff SDM
    "memindahkan" data pegawai ke akun user lain secara tidak sengaja.
    """

    class Meta:
        model = Pegawai
        fields = [
            "id",
            "nip_nidn",
            "nama_lengkap",
            "jenis_pegawai",
            "unit_kerja",
        ]
        read_only_fields = ["id"]

    def validate_nip_nidn(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("NIP/NIDN tidak boleh kosong.")
        return value

    def validate(self, attrs):
        """
        Cegah perubahan jenis_pegawai dari 'dosen' ke 'tendik' (atau
        sebaliknya) kalau pegawai yang bersangkutan sudah punya riwayat
        jabatan akademik - karena jabatan akademik khusus untuk dosen
        (lihat validasi serupa di RiwayatJabatanAkademik.clean()).
        """
        instance = getattr(self, "instance", None)
        jenis_baru = attrs.get("jenis_pegawai")

        if instance and jenis_baru and jenis_baru != instance.jenis_pegawai:
            sudah_punya_riwayat_akademik = (
                instance.jenis_pegawai == Pegawai.JenisPegawai.DOSEN
                and instance.riwayat_jabatan_akademik.exists()
            )
            if sudah_punya_riwayat_akademik:
                raise serializers.ValidationError(
                    {
                        "jenis_pegawai": (
                            "Tidak dapat mengubah jenis pegawai karena "
                            "pegawai ini sudah memiliki riwayat jabatan "
                            "akademik."
                        )
                    }
                )

        return attrs