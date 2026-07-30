from rest_framework import serializers

from .models import DataPendukung


class DataPendukungSerializer(serializers.ModelSerializer):
    """
    Serializer READ & WRITE untuk data pendukung pegawai (PEG-02).

    Dipakai untuk Staff SDM (akses semua) maupun Pegawai (akses miliknya
    sendiri) - field yang writable sama untuk keduanya, pembatasan akses
    dilakukan lewat permission & queryset di level view, bukan lewat
    serializer terpisah.

    `pegawai` writable HANYA saat create (Staff SDM menentukan pemilik
    record saat onboarding). Setelah record ada (update), field ini
    dijadikan read-only lewat get_fields() - bukan hanya dibuang di
    update() - supaya DRF juga melewati validasi field ini (termasuk
    UniqueValidator otomatis dari OneToOneField.unique=True), yang kalau
    tidak akan menolak request dengan 400 saat pegawai lain yang dikirim
    sudah punya DataPendukung sendiri, alih-alih mengabaikannya.
    """

    nama_lengkap = serializers.CharField(source="pegawai.nama_lengkap", read_only=True)
    nip_nidn = serializers.CharField(source="pegawai.nip_nidn", read_only=True)

    class Meta:
        model = DataPendukung
        fields = [
            "id",
            "pegawai",
            "nama_lengkap",
            "nip_nidn",
            "alamat",
            "kontak_darurat_nama",
            "kontak_darurat_hubungan",
            "kontak_darurat_no_hp",
            "email_kedua",
            "no_hp",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id"]

    def get_fields(self):
        fields = super().get_fields()

        if self.instance is not None:
            fields["pegawai"].read_only = True

        return fields
