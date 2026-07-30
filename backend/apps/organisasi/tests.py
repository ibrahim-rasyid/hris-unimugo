from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from apps.accounts.models import Role, User
from .models import JabatanStrukturalMaster


class JabatanStrukturalMasterViewSetTestBase(APITestCase):
    """
    Setup data dasar untuk semua test JabatanStrukturalMasterViewSet:
    - Role: admin, staff_sdm, dosen
    - User: admin, staff SDM, dosen
    - JabatanStrukturalMaster: satu record aktif, satu record nonaktif
    """

    def setUp(self):
        self.role_admin, _ = Role.objects.get_or_create(nama_role=Role.NamaRole.ADMIN)
        self.role_staff_sdm, _ = Role.objects.get_or_create(
            nama_role=Role.NamaRole.STAFF_SDM
        )
        self.role_dosen, _ = Role.objects.get_or_create(
            nama_role=Role.NamaRole.DOSEN
        )

        self.user_admin = User.objects.create_user(
            username="admin1", password="pass12345", role=self.role_admin
        )
        self.user_staff_sdm = User.objects.create_user(
            username="sdm1", password="pass12345", role=self.role_staff_sdm
        )
        self.user_dosen = User.objects.create_user(
            username="dosen1", password="pass12345", role=self.role_dosen
        )

        self.jabatan_aktif = JabatanStrukturalMaster.objects.create(
            nama_jabatan="Kaprodi", level=3, aktif=True
        )
        self.jabatan_nonaktif = JabatanStrukturalMaster.objects.create(
            nama_jabatan="Kajur (dihapus)", level=3, aktif=False
        )

        self.list_url = reverse("jabatan-struktural-master-list")

    def detail_url(self, jabatan):
        return reverse("jabatan-struktural-master-detail", args=[jabatan.id])


class JabatanStrukturalMasterTest(JabatanStrukturalMasterViewSetTestBase):
    def test_admin_create_master_berhasil(self):
        self.client.force_authenticate(user=self.user_admin)
        response = self.client.post(
            self.list_url,
            {"nama_jabatan": "Dekan", "level": 2, "aktif": True},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            JabatanStrukturalMaster.objects.filter(nama_jabatan="Dekan").exists()
        )

    def test_admin_update_master_berhasil(self):
        self.client.force_authenticate(user=self.user_admin)
        response = self.client.patch(
            self.detail_url(self.jabatan_aktif), {"level": 4}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.jabatan_aktif.refresh_from_db()
        self.assertEqual(self.jabatan_aktif.level, 4)

    def test_admin_delete_master_berhasil(self):
        self.client.force_authenticate(user=self.user_admin)
        response = self.client.delete(self.detail_url(self.jabatan_nonaktif))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            JabatanStrukturalMaster.objects.filter(
                id=self.jabatan_nonaktif.id
            ).exists()
        )

    def test_staff_sdm_create_master_ditolak(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {"nama_jabatan": "Dekan", "level": 2, "aktif": True},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_sdm_list_master_berhasil(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nama_list = [item["nama_jabatan"] for item in response.data["results"]]
        self.assertIn("Kaprodi", nama_list)

    def test_dosen_list_master_berhasil(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nama_list = [item["nama_jabatan"] for item in response.data["results"]]
        self.assertIn("Kaprodi", nama_list)
