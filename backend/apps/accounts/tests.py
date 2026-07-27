from django.test import TestCase
from rest_framework.test import APIRequestFactory

from apps.accounts.models import Role, User
from apps.accounts.permissions import IsAdmin, IsStaffSDM, IsOwnerOrStaffSDM
from apps.pegawai.models import Pegawai
from apps.data_pendukung.models import DataPendukung


class PermissionTestBase(TestCase):
    """
    Setup data dasar yang dipakai ulang di semua test permission:
    - 4 role (admin, staff_sdm, dosen, tendik)
    - 1 user + pegawai per role yang relevan (dosen jadi 'pemilik data')
    - 1 user + pegawai dosen kedua sebagai 'pegawai lain' untuk uji negatif
    - DataPendukung milik pegawai dosen pertama
    """

    def setUp(self):
        self.factory = APIRequestFactory()

        self.role_admin = Role.objects.get_or_create(nama_role=Role.NamaRole.ADMIN)
        self.role_staff_sdm = Role.objects.get_or_create(nama_role=Role.NamaRole.STAFF_SDM)
        self.role_dosen = Role.objects.get_or_create(nama_role=Role.NamaRole.DOSEN)
        self.role_tendik = Role.objects.get_or_create(nama_role=Role.NamaRole.TENDIK)

        self.user_admin = User.objects.create_user(
            username="admin1", password="pass12345", role=self.role_admin[0]
        )
        self.user_staff_sdm = User.objects.create_user(
            username="sdm1", password="pass12345", role=self.role_staff_sdm[0]
        )
        self.user_dosen = User.objects.create_user(
            username="dosen1", password="pass12345", role=self.role_dosen[0]
        )
        self.user_dosen_lain = User.objects.create_user(
            username="dosen2", password="pass12345", role=self.role_dosen[0]
        )
        self.user_tendik = User.objects.create_user(
            username="tendik1", password="pass12345", role=self.role_tendik[0]
        )

        self.pegawai_dosen = Pegawai.objects.create(
            user=self.user_dosen,
            nip_nidn="D001",
            nama_lengkap="Dosen Satu",
            jenis_pegawai=Pegawai.JenisPegawai.DOSEN,
            unit_kerja="Fakultas Teknik",
        )
        self.pegawai_dosen_lain = Pegawai.objects.create(
            user=self.user_dosen_lain,
            nip_nidn="D002",
            nama_lengkap="Dosen Dua",
            jenis_pegawai=Pegawai.JenisPegawai.DOSEN,
            unit_kerja="Fakultas Teknik",
        )

        self.data_pendukung = DataPendukung.objects.create(
            pegawai=self.pegawai_dosen,
            alamat="Jl. Contoh No. 1",
            no_hp="081234567890",
        )

    def make_request(self, method="get", user=None):
        """Helper membuat request DRF dengan user tertentu ter-autentikasi."""
        factory_method = getattr(self.factory, method.lower())
        request = factory_method("/fake-endpoint/")
        request.user = user
        return request


class IsAdminPermissionTest(PermissionTestBase):
    def setUp(self):
        super().setUp()
        self.permission = IsAdmin()

    def test_admin_diizinkan(self):
        request = self.make_request(user=self.user_admin)
        self.assertTrue(self.permission.has_permission(request, view=None))

    def test_staff_sdm_ditolak(self):
        request = self.make_request(user=self.user_staff_sdm)
        self.assertFalse(self.permission.has_permission(request, view=None))

    def test_dosen_ditolak(self):
        request = self.make_request(user=self.user_dosen)
        self.assertFalse(self.permission.has_permission(request, view=None))

    def test_user_tidak_terautentikasi_ditolak(self):
        request = self.make_request(user=None)
        request.user = type("Anon", (), {"is_authenticated": False})()
        self.assertFalse(self.permission.has_permission(request, view=None))


class IsStaffSDMPermissionTest(PermissionTestBase):
    def setUp(self):
        super().setUp()
        self.permission = IsStaffSDM()

    def test_staff_sdm_diizinkan(self):
        request = self.make_request(user=self.user_staff_sdm)
        self.assertTrue(self.permission.has_permission(request, view=None))

    def test_admin_ditolak(self):
        request = self.make_request(user=self.user_admin)
        self.assertFalse(self.permission.has_permission(request, view=None))

    def test_dosen_ditolak(self):
        request = self.make_request(user=self.user_dosen)
        self.assertFalse(self.permission.has_permission(request, view=None))

    def test_tendik_ditolak(self):
        request = self.make_request(user=self.user_tendik)
        self.assertFalse(self.permission.has_permission(request, view=None))


class IsOwnerOrStaffSDMPermissionTest(PermissionTestBase):
    def setUp(self):
        super().setUp()
        self.permission = IsOwnerOrStaffSDM()

    # --- has_permission (level akses awal) ---

    def test_has_permission_staff_sdm_diizinkan(self):
        request = self.make_request(user=self.user_staff_sdm)
        self.assertTrue(self.permission.has_permission(request, view=None))

    def test_has_permission_dosen_diizinkan(self):
        request = self.make_request(user=self.user_dosen)
        self.assertTrue(self.permission.has_permission(request, view=None))

    def test_has_permission_tendik_diizinkan(self):
        request = self.make_request(user=self.user_tendik)
        self.assertTrue(self.permission.has_permission(request, view=None))

    def test_has_permission_admin_ditolak(self):
        """
        Admin tidak termasuk aktor yang mengurus data pendukung/data
        pribadi pegawai sesuai use case (Admin hanya setup role).
        """
        request = self.make_request(user=self.user_admin)
        self.assertFalse(self.permission.has_permission(request, view=None))

    # --- has_object_permission: Staff SDM (akses penuh) ---

    def test_object_permission_staff_sdm_boleh_read_data_siapa_saja(self):
        request = self.make_request(method="get", user=self.user_staff_sdm)
        self.assertTrue(
            self.permission.has_object_permission(
                request, view=None, obj=self.data_pendukung
            )
        )

    def test_object_permission_staff_sdm_boleh_write_data_siapa_saja(self):
        request = self.make_request(method="patch", user=self.user_staff_sdm)
        self.assertTrue(
            self.permission.has_object_permission(
                request, view=None, obj=self.data_pendukung
            )
        )

    # --- has_object_permission: Pegawai mengakses miliknya sendiri ---

    def test_object_permission_pegawai_boleh_read_milik_sendiri(self):
        request = self.make_request(method="get", user=self.user_dosen)
        self.assertTrue(
            self.permission.has_object_permission(
                request, view=None, obj=self.data_pendukung
            )
        )

    def test_object_permission_pegawai_boleh_write_milik_sendiri(self):
        request = self.make_request(method="patch", user=self.user_dosen)
        self.assertTrue(
            self.permission.has_object_permission(
                request, view=None, obj=self.data_pendukung
            )
        )

    # --- has_object_permission: Pegawai mengakses milik pegawai LAIN (harus ditolak) ---

    def test_object_permission_pegawai_ditolak_read_milik_orang_lain(self):
        request = self.make_request(method="get", user=self.user_dosen_lain)
        self.assertFalse(
            self.permission.has_object_permission(
                request, view=None, obj=self.data_pendukung
            )
        )

    def test_object_permission_pegawai_ditolak_write_milik_orang_lain(self):
        request = self.make_request(method="patch", user=self.user_dosen_lain)
        self.assertFalse(
            self.permission.has_object_permission(
                request, view=None, obj=self.data_pendukung
            )
        )

    # --- has_object_permission: objek langsung berupa Pegawai (kasus PEG-01 lihat data pribadi) ---

    def test_object_permission_pegawai_boleh_lihat_profil_pegawai_sendiri(self):
        request = self.make_request(method="get", user=self.user_dosen)
        self.assertTrue(
            self.permission.has_object_permission(
                request, view=None, obj=self.pegawai_dosen
            )
        )

    def test_object_permission_pegawai_ditolak_lihat_profil_pegawai_lain(self):
        request = self.make_request(method="get", user=self.user_dosen)
        self.assertFalse(
            self.permission.has_object_permission(
                request, view=None, obj=self.pegawai_dosen_lain
            )
        )