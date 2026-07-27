from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from apps.accounts.models import Role, User
from .models import Pegawai


class PegawaiViewSetTestBase(APITestCase):
    """
    Setup data dasar untuk semua test PegawaiViewSet:
    - Role: staff_sdm, dosen
    - User + Pegawai: staff SDM, dosen A (pemilik), dosen B (pegawai lain)
    """

    def setUp(self):
        self.role_staff_sdm, _ = Role.objects.get_or_create(
            nama_role=Role.NamaRole.STAFF_SDM
        )
        self.role_dosen, _ = Role.objects.get_or_create(
            nama_role=Role.NamaRole.DOSEN
        )

        self.user_staff_sdm = User.objects.create_user(
            username="sdm1", password="pass12345", role=self.role_staff_sdm
        )
        self.user_dosen = User.objects.create_user(
            username="dosen1", password="pass12345", role=self.role_dosen
        )
        self.user_dosen_lain = User.objects.create_user(
            username="dosen2", password="pass12345", role=self.role_dosen
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

        self.list_url = reverse("pegawai-list")

    def detail_url(self, pegawai):
        return reverse("pegawai-detail", args=[pegawai.id])


class PegawaiListTest(PegawaiViewSetTestBase):
    def test_staff_sdm_melihat_semua_pegawai(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nip_list = [item["nip_nidn"] for item in response.data["results"]]
        self.assertIn("D001", nip_list)
        self.assertIn("D002", nip_list)

    def test_dosen_hanya_melihat_dirinya_sendiri(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nip_list = [item["nip_nidn"] for item in response.data["results"]]
        self.assertEqual(nip_list, ["D001"])
        self.assertNotIn("D002", nip_list)

    def test_user_tidak_terautentikasi_ditolak(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PegawaiRetrieveTest(PegawaiViewSetTestBase):
    def test_dosen_retrieve_data_sendiri_berhasil(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.detail_url(self.pegawai_dosen))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nip_nidn"], "D001")

    def test_dosen_retrieve_data_pegawai_lain_gagal(self):
        """
        Karena get_queryset() sudah memfilter berdasarkan kepemilikan,
        pegawai lain dianggap 'tidak ada' (404), bukan 403 -
        objeknya memang tidak pernah masuk queryset dosen ini.
        """
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.detail_url(self.pegawai_dosen_lain))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_sdm_retrieve_pegawai_manapun_berhasil(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.get(self.detail_url(self.pegawai_dosen_lain))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nip_nidn"], "D002")


class PegawaiUpdateTest(PegawaiViewSetTestBase):
    def test_staff_sdm_update_berhasil(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.patch(
            self.detail_url(self.pegawai_dosen),
            {"unit_kerja": "Fakultas Ekonomi"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pegawai_dosen.refresh_from_db()
        self.assertEqual(self.pegawai_dosen.unit_kerja, "Fakultas Ekonomi")

    def test_dosen_update_data_sendiri_ditolak(self):
        """
        Pegawai TIDAK BOLEH mengubah data induknya sendiri lewat endpoint
        ini - hanya Staff SDM yang berhak (SDM-01). Update data pribadi
        pegawai lewat DataPendukung, bukan endpoint ini.
        """
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.patch(
            self.detail_url(self.pegawai_dosen),
            {"unit_kerja": "Fakultas Ekonomi"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.pegawai_dosen.refresh_from_db()
        self.assertEqual(self.pegawai_dosen.unit_kerja, "Fakultas Teknik")

    def test_dosen_update_data_pegawai_lain_ditolak(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.patch(
            self.detail_url(self.pegawai_dosen_lain),
            {"unit_kerja": "Fakultas Ekonomi"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_pegawai_tidak_diizinkan(self):
        """
        Endpoint create sengaja dinonaktifkan (http_method_names) sampai
        alur pembuatan pegawai baru (sekaligus User) dirancang terpisah.
        """
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "nip_nidn": "D003",
                "nama_lengkap": "Dosen Tiga",
                "jenis_pegawai": Pegawai.JenisPegawai.DOSEN,
                "unit_kerja": "Fakultas Teknik",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)