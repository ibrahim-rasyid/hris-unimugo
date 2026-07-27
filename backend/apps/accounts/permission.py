from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Role


class IsAdmin(BasePermission):
    """
    Hanya role Admin yang boleh mengakses.
    Dipakai untuk endpoint setup role & kelola akun (ADM-01, ADM-02, ADM-03).
    """

    message = "Hanya Admin yang dapat mengakses endpoint ini."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role
            and user.role.nama_role == Role.NamaRole.ADMIN
        )


class IsStaffSDM(BasePermission):
    """
    Hanya role Staff SDM yang boleh mengakses.
    Dipakai untuk endpoint CRUD data pegawai & semua riwayat
    (SDM-01 s.d. SDM-06).
    """

    message = "Hanya Staff SDM yang dapat mengakses endpoint ini."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role
            and user.role.nama_role == Role.NamaRole.STAFF_SDM
        )


class IsOwnerOrStaffSDM(BasePermission):
    """
    Dipakai khusus untuk endpoint DataPendukung (PEG-02) dan
    endpoint lihat data pribadi (PEG-01):
    - Staff SDM: read-write penuh ke semua data
    - Pegawai: hanya boleh akses (read/write) miliknya sendiri,
      write HANYA untuk metode aman + PATCH/PUT ke objek miliknya
    - Role lain (misal Admin): ditolak - endpoint ini bukan urusan Admin
    """

    message = "Anda hanya dapat mengakses data milik Anda sendiri."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.role):
            return False
        return user.role.nama_role in (
            Role.NamaRole.STAFF_SDM,
            Role.NamaRole.DOSEN,
            Role.NamaRole.TENDIK,
        )

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Staff SDM: akses penuh ke semua objek.
        if user.role.nama_role == Role.NamaRole.STAFF_SDM:
            return True

        # Pegawai (dosen/tendik): hanya boleh ke objek miliknya sendiri.
        # `obj` diasumsikan punya atribut `pegawai` (FK ke Pegawai),
        # atau `obj` itu sendiri adalah instance Pegawai.
        pegawai_pemilik = obj.pegawai if hasattr(obj, "pegawai") else obj
        is_owner = (
            hasattr(pegawai_pemilik, "user_id")
            and pegawai_pemilik.user_id == user.id
        )

        if not is_owner:
            return False

        # Pegawai boleh read (GET/HEAD/OPTIONS) data miliknya kapan saja.
        if request.method in SAFE_METHODS:
            return True

        # Untuk write (PATCH/PUT), izinkan - pembatasan FIELD mana yang
        # boleh diubah pegawai dilakukan di level SERIALIZER, bukan di sini.
        # Permission ini hanya menjamin kepemilikan objek, bukan field.
        return True