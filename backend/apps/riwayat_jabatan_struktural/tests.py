from datetime import date

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from apps.accounts.models import Role, User
from apps.organisasi.models import JabatanStrukturalMaster
from apps.pegawai.models import Pegawai
from .models import RiwayatJabatanStruktural


class RiwayatJabatanStrukturalViewSetTestBase(APITestCase):
    """
    Setup data dasar untuk semua test RiwayatJabatanStrukturalViewSet:
    - Role: staff_sdm, dosen
    - User + Pegawai: staff SDM, dosen A (pemilik), dosen B (pegawai lain)
    - JabatanStrukturalMaster: satu record aktif (Kaprodi), satu record
      nonaktif (Kajur)
    - RiwayatJabatanStruktural: satu record milik dosen A (masih menjabat),
      satu milik dosen B (sudah selesai)
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

        self.jabatan_kaprodi = JabatanStrukturalMaster.objects.create(
            nama_jabatan="Kaprodi", level=3, aktif=True
        )
        self.jabatan_dekan = JabatanStrukturalMaster.objects.create(
            nama_jabatan="Dekan", level=2, aktif=True
        )
        self.jabatan_nonaktif = JabatanStrukturalMaster.objects.create(
            nama_jabatan="Kajur (dihapus)", level=3, aktif=False
        )

        self.riwayat_dosen = RiwayatJabatanStruktural.objects.create(
            pegawai=self.pegawai_dosen,
            jabatan=self.jabatan_kaprodi,
            tmt=date(2018, 1, 1),
        )
        self.riwayat_dosen_lain = RiwayatJabatanStruktural.objects.create(
            pegawai=self.pegawai_dosen_lain,
            jabatan=self.jabatan_dekan,
            tmt=date(2015, 1, 1),
            selesai=date(2019, 1, 1),
        )

        self.list_url = reverse("riwayat-jabatan-struktural-list")

    def detail_url(self, riwayat):
        return reverse("riwayat-jabatan-struktural-detail", args=[riwayat.id])


class RiwayatJabatanStrukturalListTest(RiwayatJabatanStrukturalViewSetTestBase):
    def test_staff_sdm_melihat_semua_riwayat_jabatan_struktural(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pegawai_ids = [str(item["pegawai"]) for item in response.data["results"]]
        self.assertIn(str(self.pegawai_dosen.id), pegawai_ids)
        self.assertIn(str(self.pegawai_dosen_lain.id), pegawai_ids)

    def test_dosen_hanya_melihat_riwayat_jabatan_struktural_sendiri(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pegawai_ids = [str(item["pegawai"]) for item in response.data["results"]]
        self.assertEqual(pegawai_ids, [str(self.pegawai_dosen.id)])
        self.assertNotIn(str(self.pegawai_dosen_lain.id), pegawai_ids)

    def test_user_tidak_terautentikasi_ditolak(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RiwayatJabatanStrukturalRetrieveTest(RiwayatJabatanStrukturalViewSetTestBase):
    def test_dosen_retrieve_riwayat_sendiri_berhasil(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.detail_url(self.riwayat_dosen))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["jabatan"]["nama_jabatan"], "Kaprodi")
        self.assertTrue(response.data["masih_menjabat"])

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
        self.assertEqual(response.data["jabatan"]["nama_jabatan"], "Dekan")
        self.assertFalse(response.data["masih_menjabat"])


class RiwayatJabatanStrukturalCreateTest(RiwayatJabatanStrukturalViewSetTestBase):
    def test_staff_sdm_create_riwayat_jabatan_struktural_berhasil(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jabatan": str(self.jabatan_dekan.id),
                "tmt": "2022-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            RiwayatJabatanStruktural.objects.filter(
                pegawai=self.pegawai_dosen,
                jabatan=self.jabatan_dekan,
            ).exists()
        )

    def test_dosen_create_riwayat_jabatan_struktural_ditolak(self):
        """
        Create riwayat jabatan struktural adalah wewenang Staff SDM
        (SDM-05), bukan pegawai - meskipun pegawai membuat riwayat untuk
        dirinya sendiri.
        """
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jabatan": str(self.jabatan_dekan.id),
                "tmt": "2022-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            RiwayatJabatanStruktural.objects.filter(
                pegawai=self.pegawai_dosen,
                jabatan=self.jabatan_dekan,
            ).exists()
        )

    def test_create_selesai_lebih_awal_dari_tmt_ditolak(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jabatan": str(self.jabatan_dekan.id),
                "tmt": "2022-01-01",
                "selesai": "2021-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("selesai", response.data)

    def test_create_jabatan_nonaktif_ditolak(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jabatan": str(self.jabatan_nonaktif.id),
                "tmt": "2022-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("jabatan", response.data)

    def test_create_tanpa_selesai_masih_menjabat(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jabatan": str(self.jabatan_dekan.id),
                "tmt": "2022-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        detail_response = self.client.get(
            reverse("riwayat-jabatan-struktural-detail", args=[response.data["id"]])
        )
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertTrue(detail_response.data["masih_menjabat"])
        self.assertIsNone(detail_response.data["selesai"])


class RiwayatJabatanStrukturalDeleteTest(RiwayatJabatanStrukturalViewSetTestBase):
    def test_staff_sdm_delete_riwayat_tidak_diizinkan(self):
        """
        Endpoint delete sengaja dinonaktifkan (http_method_names) karena
        riwayat jabatan struktural bersifat append-only - koreksi harus
        lewat record baru, bukan penghapusan record lama.
        """
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.delete(self.detail_url(self.riwayat_dosen))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(
            RiwayatJabatanStruktural.objects.filter(id=self.riwayat_dosen.id).exists()
        )
