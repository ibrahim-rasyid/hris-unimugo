from rest_framework import permissions, viewsets

from apps.accounts.models import Role
from apps.accounts.permissions import IsOwnerOrStaffSDM, IsStaffSDM

from .models import RiwayatKepangkatan
from .serializers import (
    RiwayatKepangkatanListSerializer,
    RiwayatKepangkatanWriteSerializer,
)


class RiwayatKepangkatanViewSet(viewsets.ModelViewSet):
    """
    Endpoint riwayat kepangkatan/golongan pegawai (SDM-03).

    Aturan akses:
    - Staff SDM: read & write (create/update) ke SEMUA riwayat kepangkatan.
    - Pegawai (dosen/tendik): read-only, HANYA ke riwayat kepangkatan
      miliknya sendiri (PEG-01).
    - Admin: tidak berhak akses endpoint ini.

    Catatan: `delete` sengaja TIDAK diaktifkan - riwayat kepangkatan
    bersifat historikal/append-only (lihat Aturan Wajib #2 di CLAUDE.md).
    Kalau ada kesalahan input, tambahkan record koreksi baru, jangan
    hapus record lama.
    """

    http_method_names = ["get", "post", "put", "patch", "head", "options"]
    queryset = RiwayatKepangkatan.objects.select_related(
        "pegawai", "pegawai__user"
    ).all()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RiwayatKepangkatanWriteSerializer
        return RiwayatKepangkatanListSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            # Hanya Staff SDM yang boleh menambah/mengubah riwayat kepangkatan.
            return [permissions.IsAuthenticated(), IsStaffSDM()]
        # list & retrieve: dicek lebih lanjut lewat get_queryset (filter data)
        # dan has_object_permission (pembatasan akses ke objek tunggal).
        return [permissions.IsAuthenticated(), IsOwnerOrStaffSDM()]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        if not user.is_authenticated or not user.role:
            return qs.none()

        if user.role.nama_role == Role.NamaRole.STAFF_SDM:
            return qs

        if user.role.nama_role in (Role.NamaRole.DOSEN, Role.NamaRole.TENDIK):
            return qs.filter(pegawai__user=user)

        # Role lain (misal Admin) tidak berhak melihat riwayat kepangkatan sama sekali.
        return qs.none()
