from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from apps.accounts.models import Role, User
from apps.pegawai.models import Pegawai
from .models import DataPendukung


class DataPendukungViewSetTestBase(APITestCase):
    """
    Setup data dasar untuk semua test DataPendukungViewSet:
    - Role: staff_sdm, dosen
    - User + Pegawai: staff SDM, dosen A (pemilik), dosen B (pegawai lain)
    - DataPendukung: satu record milik dosen A, satu milik dosen B
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

        self.data_dosen = DataPendukung.objects.create(
            pegawai=self.pegawai_dosen,
            alamat="Jl. Contoh No. 1",
            no_hp="081200000001",
        )
        self.data_dosen_lain = DataPendukung.objects.create(
            pegawai=self.pegawai_dosen_lain,
            alamat="Jl. Contoh No. 2",
            no_hp="081200000002",
        )

        self.list_url = reverse("data-pendukung-list")

    def detail_url(self, data):
        return reverse("data-pendukung-detail", args=[data.id])


class DataPendukungCreateTest(DataPendukungViewSetTestBase):
    def test_staff_sdm_create_data_pendukung_berhasil(self):
        pegawai_baru_user = User.objects.create_user(
            username="dosen3", password="pass12345", role=self.role_dosen
        )
        pegawai_baru = Pegawai.objects.create(
            user=pegawai_baru_user,
            nip_nidn="D003",
            nama_lengkap="Dosen Tiga",
            jenis_pegawai=Pegawai.JenisPegawai.DOSEN,
            unit_kerja="Fakultas Teknik",
        )

        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.post(
            self.list_url,
            {"pegawai": str(pegawai_baru.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            DataPendukung.objects.filter(pegawai=pegawai_baru).exists()
        )

    def test_pegawai_create_data_pendukung_ditolak(self):
        pegawai_baru_user = User.objects.create_user(
            username="dosen4", password="pass12345", role=self.role_dosen
        )
        pegawai_baru = Pegawai.objects.create(
            user=pegawai_baru_user,
            nip_nidn="D004",
            nama_lengkap="Dosen Empat",
            jenis_pegawai=Pegawai.JenisPegawai.DOSEN,
            unit_kerja="Fakultas Teknik",
        )

        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.post(
            self.list_url,
            {"pegawai": str(pegawai_baru.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            DataPendukung.objects.filter(pegawai=pegawai_baru).exists()
        )


class DataPendukungUpdateTest(DataPendukungViewSetTestBase):
    def test_pegawai_update_data_pendukung_sendiri_berhasil(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.patch(
            self.detail_url(self.data_dosen),
            {"no_hp": "081299999999", "alamat": "Alamat Baru"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.data_dosen.refresh_from_db()
        self.assertEqual(self.data_dosen.no_hp, "081299999999")
        self.assertEqual(self.data_dosen.alamat, "Alamat Baru")

    def test_pegawai_update_data_pendukung_pegawai_lain_ditolak(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.patch(
            self.detail_url(self.data_dosen_lain),
            {"no_hp": "081200000099"},
        )

        self.assertIn(
            response.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND),
        )
        self.data_dosen_lain.refresh_from_db()
        self.assertEqual(self.data_dosen_lain.no_hp, "081200000002")

    def test_pegawai_ubah_field_pegawai_diabaikan(self):
        """
        Field `pegawai` read-only setelah dibuat - kalau pegawai mencoba
        mengirim field ini (misal mencoba reassign ke dirinya sendiri),
        request harus tetap berhasil untuk field lain, tapi kepemilikan
        record TIDAK berubah.
        """
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.patch(
            self.detail_url(self.data_dosen),
            {
                "pegawai": str(self.pegawai_dosen_lain.id),
                "no_hp": "081211112222",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.data_dosen.refresh_from_db()
        self.assertEqual(self.data_dosen.pegawai_id, self.pegawai_dosen.id)
        self.assertEqual(self.data_dosen.no_hp, "081211112222")


class DataPendukungListTest(DataPendukungViewSetTestBase):
    def test_staff_sdm_melihat_semua_data_pendukung(self):
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pegawai_ids = [str(item["pegawai"]) for item in response.data["results"]]
        self.assertIn(str(self.pegawai_dosen.id), pegawai_ids)
        self.assertIn(str(self.pegawai_dosen_lain.id), pegawai_ids)

    def test_dosen_hanya_melihat_data_pendukung_sendiri(self):
        self.client.force_authenticate(user=self.user_dosen)
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pegawai_ids = [str(item["pegawai"]) for item in response.data["results"]]
        self.assertEqual(pegawai_ids, [str(self.pegawai_dosen.id)])
        self.assertNotIn(str(self.pegawai_dosen_lain.id), pegawai_ids)

    def test_user_tidak_terautentikasi_ditolak(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DataPendukungDeleteTest(DataPendukungViewSetTestBase):
    def test_staff_sdm_delete_data_pendukung_tidak_diizinkan(self):
        """
        Endpoint delete sengaja dinonaktifkan (http_method_names) - setiap
        pegawai harus selalu punya tepat satu record DataPendukung
        (relasi 1-1), jadi tidak boleh dihapus.
        """
        self.client.force_authenticate(user=self.user_staff_sdm)
        response = self.client.delete(self.detail_url(self.data_dosen))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(DataPendukung.objects.filter(id=self.data_dosen.id).exists())
