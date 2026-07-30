from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from apps.accounts.models import Role
from apps.accounts.permissions import IsOwnerOrStaffSDM, IsStaffSDM

from .models import DataPendukung
from .serializers import DataPendukungSerializer


class DataPendukungViewSet(viewsets.ModelViewSet):
    """
    Endpoint data pendukung pegawai - SATU-SATUNYA data yang boleh
    diubah langsung oleh role Pegawai untuk dirinya sendiri (PEG-02).

    Berbeda dari viewset riwayat lain:
    - Bukan historikal - data ini diUPDATE di tempat, bukan ditambah
      sebagai record baru. `delete` tetap TIDAK diaktifkan karena setiap
      pegawai harus selalu punya tepat satu record (relasi 1-1).
    - Serializer read & write SAMA (DataPendukungSerializer) - field yang
      writable identik untuk Staff SDM maupun Pegawai, pembeda hanya
      kepemilikan objek.
    - `create` HANYA wewenang Staff SDM (saat onboarding pegawai baru,
      Staff SDM yang membuat record awal DataPendukung) - Pegawai tidak
      bisa membuat recordnya sendiri.
    """

    http_method_names = ["get", "post", "put", "patch", "head", "options"]
    serializer_class = DataPendukungSerializer
    queryset = DataPendukung.objects.select_related("pegawai", "pegawai__user").all()

    def get_permissions(self):
        if self.action == "create":
            # Hanya Staff SDM yang boleh membuat record DataPendukung baru.
            return [permissions.IsAuthenticated(), IsStaffSDM()]
        # list/retrieve/update/partial_update: pemilik ATAU Staff SDM,
        # pola aksesnya sama untuk semua operasi ini (PEG-02).
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

        # Role lain (misal Admin) tidak berhak melihat data pendukung sama sekali.
        return qs.none()

    def perform_update(self, serializer):
        """
        Defense-in-depth di luar has_object_permission: kalau yang
        mengubah adalah Pegawai (bukan Staff SDM), pastikan sekali lagi
        instance yang diupdate memang miliknya sendiri.
        """
        user = self.request.user
        instance = serializer.instance

        if user.role.nama_role != Role.NamaRole.STAFF_SDM:
            if instance.pegawai.user_id != user.id:
                raise PermissionDenied(
                    "Anda hanya dapat mengubah data pendukung milik Anda sendiri."
                )

        serializer.save()
