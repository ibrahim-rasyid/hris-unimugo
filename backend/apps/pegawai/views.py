from rest_framework import permissions, viewsets

from apps.accounts.models import Role
from apps.accounts.permissions import IsOwnerOrStaffSDM, IsStaffSDM

from .models import Pegawai
from .serializers import PegawaiListSerializer, PegawaiUpdateSerializer


class PegawaiViewSet(viewsets.ModelViewSet):
    """
    Endpoint data induk pegawai (dosen & tendik).

    Aturan akses:
    - Staff SDM: read & write ke SEMUA data pegawai (SDM-01).
    - Pegawai (dosen/tendik): read-only, HANYA ke data miliknya sendiri (PEG-01).
    - Admin: tidak berhak akses endpoint ini - di luar cakupan use case Admin.

    Catatan: `create` (pembuatan pegawai baru) sengaja TIDAK diaktifkan
    di sini. Membuat pegawai baru melibatkan pembuatan/keterkaitan User
    baru sekaligus, yang lebih aman ditangani lewat endpoint/alur terpisah
    (transaksi "buat User + buat Pegawai" perlu ditangani eksplisit,
    bukan lewat serializer update biasa).
    """

    http_method_names = ["get", "put", "patch", "head", "options"]
    queryset = Pegawai.objects.select_related("user", "user__role").all()

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return PegawaiUpdateSerializer
        return PegawaiListSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update"):
            # Hanya Staff SDM yang boleh mengubah data induk pegawai.
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
            return qs.filter(user=user)

        # Role lain (misal Admin) tidak berhak melihat data pegawai sama sekali.
        return qs.none()