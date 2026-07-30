from datetime import date

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from apps.accounts.models import Role, User
from apps.pegawai.models import Pegawai
from .models import RiwayatJabatanAkademik


class RiwayatJabatanAkademikViewSetTestBase(APITestCase):
    """
    Setup data dasar untuk semua test RiwayatJabatanAkademikViewSet:
    - Role: staff_sdm, dosen, tendik
    - User + Pegawai: staff SDM, dosen A (pemilik), dosen B (pegawai lain),
      tendik (jenis_pegawai TENDIK, untuk skenario validasi)
    - RiwayatJabatanAkademik: satu record milik dosen A, satu milik dosen B
    """

    def setUp(self):
        self.role_staff_sdm, _ = Role.objects.get_or_create(
            nama_role=Role.NamaRole.STAFF_SDM
        )
        self.role_dosen, _ = Role.objects.get_or_create(
            nama_role=Role.NamaRole.DOSEN
        )
        self.role_tendik, _ = Role.objects.get_or_create(
            nama_role=Role.NamaRole.TENDIK
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
        self.user_tendik = User.objects.create_user(
            username="tendik1", password="pass12345", role=self.role_tendik
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
        self.pegawai_tendik = Pegawai.objects.create(
            user=self.user_tendik,
            nip_nidn="T001",
            nama_lengkap="Tendik Satu",
            jenis_pegawai=Pegawai.JenisPegawai.TENDIK,
            unit_kerja="Biro Umum",
        )

        self.riwayat_dosen = RiwayatJabatanAkademik.objects.create(
            pegawai=self.pegawai_dosen,
            jabatan=RiwayatJabatanAkademik.Jabatan.ASISTEN_AHLI,
            tmt=date(2018, 1, 1),
        )
        self.riwayat_dosen_lain = RiwayatJabatanAkademik.objects.create(
            pegawai=self.pegawai_dosen_lain,
            jabatan=RiwayatJabatanAkademik.Jabatan.LEKTOR,
            tmt=date(2019, 1, 1),
        )

        self.list_url = reverse("riwayat-jabatan-akademik-list")

    def detail_url(self, riwayat):
        return reverse("riwayat-jabatan-akademik-detail", args=[riwayat.id])


class RiwayatJabatanAkademikListTest(RiwayatJabatanAkademikViewSetTestBase):
    def test_staff_sdm_melihat_semua_riwayat_jabatan_akademik(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jabatan_list = [item["jabatan"] for item in response.data["results"]]
        self.assertIn(RiwayatJabatanAkademik.Jabatan.ASISTEN_AHLI, jabatan_list)
        self.assertIn(RiwayatJabatanAkademik.Jabatan.LEKTOR, jabatan_list)

    def test_dosen_hanya_melihat_riwayat_jabatan_akademik_sendiri(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        jabatan_list = [item["jabatan"] for item in response.data["results"]]
        self.assertEqual(jabatan_list, [RiwayatJabatanAkademik.Jabatan.ASISTEN_AHLI])
        self.assertNotIn(RiwayatJabatanAkademik.Jabatan.LEKTOR, jabatan_list)

    def test_user_tidak_terautentikasi_ditolak(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RiwayatJabatanAkademikRetrieveTest(RiwayatJabatanAkademikViewSetTestBase):
    def test_dosen_retrieve_riwayat_sendiri_berhasil(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.detail_url(self.riwayat_dosen))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["jabatan"], RiwayatJabatanAkademik.Jabatan.ASISTEN_AHLI
        )

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
        self.assertEqual(
            response.data["jabatan"], RiwayatJabatanAkademik.Jabatan.LEKTOR
        )


class RiwayatJabatanAkademikCreateTest(RiwayatJabatanAkademikViewSetTestBase):
    def test_staff_sdm_create_riwayat_jabatan_akademik_berhasil(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jabatan": RiwayatJabatanAkademik.Jabatan.LEKTOR,
                "tmt": "2022-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            RiwayatJabatanAkademik.objects.filter(
                pegawai=self.pegawai_dosen,
                jabatan=RiwayatJabatanAkademik.Jabatan.LEKTOR,
            ).exists()
        )

    def test_dosen_create_riwayat_jabatan_akademik_ditolak(self):
        """
        Create riwayat jabatan akademik adalah wewenang Staff SDM (SDM-04),
        bukan pegawai - meskipun pegawai membuat riwayat untuk dirinya
        sendiri.
        """
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jabatan": RiwayatJabatanAkademik.Jabatan.LEKTOR,
                "tmt": "2022-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            RiwayatJabatanAkademik.objects.filter(
                pegawai=self.pegawai_dosen,
                jabatan=RiwayatJabatanAkademik.Jabatan.LEKTOR,
            ).exists()
        )

    def test_create_tmt_masa_depan_ditolak(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jabatan": RiwayatJabatanAkademik.Jabatan.LEKTOR,
                "tmt": "2999-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_jabatan_sama_dengan_terakhir_ditolak(self):
        """
        Jabatan aktif terakhir pegawai_dosen adalah Asisten Ahli
        (tmt 2018-01-01). Input jabatan Asisten Ahli lagi (tanpa
        perubahan) harus ditolak validasi.
        """
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_dosen.id),
                "jabatan": RiwayatJabatanAkademik.Jabatan.ASISTEN_AHLI,
                "tmt": "2023-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("jabatan", response.data)

    def test_create_untuk_pegawai_tendik_ditolak(self):
        """
        Jabatan akademik hanya berlaku untuk pegawai jenis Dosen (lihat
        clean() di model RiwayatJabatanAkademik) - create untuk pegawai
        jenis_pegawai=TENDIK harus gagal validasi.
        """
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {
                "pegawai": str(self.pegawai_tendik.id),
                "jabatan": RiwayatJabatanAkademik.Jabatan.ASISTEN_AHLI,
                "tmt": "2022-01-01",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("pegawai", response.data)
        self.assertIn(
            "hanya berlaku untuk pegawai jenis Dosen", str(response.data["pegawai"])
        )


class RiwayatJabatanAkademikDeleteTest(RiwayatJabatanAkademikViewSetTestBase):
    def test_staff_sdm_delete_riwayat_tidak_diizinkan(self):
        """
        Endpoint delete sengaja dinonaktifkan (http_method_names) karena
        riwayat jabatan akademik bersifat append-only - koreksi harus
        lewat record baru, bukan penghapusan record lama.
        """
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.delete(self.detail_url(self.riwayat_dosen))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(
            RiwayatJabatanAkademik.objects.filter(id=self.riwayat_dosen.id).exists()
        )
