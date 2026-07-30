from datetime import date

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from apps.accounts.models import Role, User
from apps.pegawai.models import Pegawai
from .models import RiwayatStudi


class RiwayatStudiViewSetTestBase(APITestCase):
    """
    Setup data dasar untuk semua test RiwayatStudiViewSet:
    - Role: staff_sdm, dosen
    - User + Pegawai: staff SDM, dosen A (pemilik), dosen B (pegawai lain)
    - RiwayatStudi: satu record milik dosen A, satu milik dosen B
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

        self.riwayat_dosen = RiwayatStudi.objects.create(
            pegawai=self.pegawai_dosen,
            jenjang=RiwayatStudi.Jenjang.S2,
            institusi="Universitas Indonesia",
            gelar="M.Kom",
            tahun_lulus=date(2015, 8, 1),
        )
        self.riwayat_dosen_lain = RiwayatStudi.objects.create(
            pegawai=self.pegawai_dosen_lain,
            jenjang=RiwayatStudi.Jenjang.S2,
            institusi="Institut Teknologi Bandung",
            gelar="M.T",
            tahun_lulus=date(2016, 8, 1),
        )

        self.list_url = reverse("riwayat-studi-list")

    def detail_url(self, riwayat):
        return reverse("riwayat-studi-detail", args=[riwayat.id])


class RiwayatStudiListTest(RiwayatStudiViewSetTestBase):
    def test_staff_sdm_melihat_semua_riwayat_studi(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        institusi_list = [item["institusi"] for item in response.data["results"]]
        self.assertIn("Universitas Indonesia", institusi_list)
        self.assertIn("Institut Teknologi Bandung", institusi_list)

    def test_dosen_hanya_melihat_riwayat_studi_sendiri(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        institusi_list = [item["institusi"] for item in response.data["results"]]
        self.assertEqual(institusi_list, ["Universitas Indonesia"])
        self.assertNotIn("Institut Teknologi Bandung", institusi_list)

    def test_user_tidak_terautentikasi_ditolak(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RiwayatStudiRetrieveTest(RiwayatStudiViewSetTestBase):
    def test_dosen_retrieve_riwayat_sendiri_berhasil(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.detail_url(self.riwayat_dosen))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["institusi"], "Universitas Indonesia")

    def test_dosen_retrieve_riwayat_pegawai_lain_gagal(self):
        """
        Karena get_queryset() sudah memfilter berdasarkan kepemilikan,
        riwayat pegawai lain dianggap 'tidak ada' (404).
        """
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.detail_url(self.riwayat_dosen_lain))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_sdm_retrieve_riwayat_manapun_berhasil(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.get(self.detail_url(self.riwayat_dosen_lain))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["institusi"], "Institut Teknologi Bandung")


class RiwayatStudiCreateTest(RiwayatStudiViewSetTestBase):
    def test_staff_sdm_create_riwayat_studi_berhasil(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jenjang": RiwayatStudi.Jenjang.S3,
                "institusi": "Universitas Gadjah Mada",
                "gelar": "Dr.",
                "tahun_lulus": "2022-08-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            RiwayatStudi.objects.filter(
                pegawai=self.pegawai_dosen, institusi="Universitas Gadjah Mada"
            ).exists()
        )

    def test_dosen_create_riwayat_studi_ditolak(self):
        """
        Create riwayat studi adalah wewenang Staff SDM (SDM-02), bukan
        pegawai - meskipun pegawai membuat riwayat untuk dirinya sendiri.
        """
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jenjang": RiwayatStudi.Jenjang.S3,
                "institusi": "Universitas Gadjah Mada",
                "gelar": "Dr.",
                "tahun_lulus": "2022-08-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            RiwayatStudi.objects.filter(institusi="Universitas Gadjah Mada").exists()
        )

    def test_create_tahun_lulus_masa_depan_ditolak(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jenjang": RiwayatStudi.Jenjang.S3,
                "institusi": "Universitas Gadjah Mada",
                "gelar": "Dr.",
                "tahun_lulus": "2999-08-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RiwayatStudiDeleteTest(RiwayatStudiViewSetTestBase):
    def test_staff_sdm_delete_riwayat_tidak_diizinkan(self):
        """
        Endpoint delete sengaja dinonaktifkan (http_method_names) karena
        riwayat studi bersifat append-only - koreksi harus lewat record
        baru, bukan penghapusan record lama.
        """
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.delete(self.detail_url(self.riwayat_dosen))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(RiwayatStudi.objects.filter(id=self.riwayat_dosen.id).exists())
