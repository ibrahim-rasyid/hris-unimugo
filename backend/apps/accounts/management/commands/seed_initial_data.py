import datetime

from decouple import config
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Role, User
from apps.data_pendukung.models import DataPendukung
from apps.organisasi.models import JabatanStrukturalMaster
from apps.pegawai.models import Pegawai
from apps.riwayat_jabatan_akademik.models import RiwayatJabatanAkademik
from apps.riwayat_jabatan_struktural.models import RiwayatJabatanStruktural
from apps.riwayat_kepangkatan.models import RiwayatKepangkatan
from apps.riwayat_studi.models import RiwayatStudi

# Password contoh untuk akun dummy (Staff SDM & Pegawai). HANYA untuk
# development/testing - jangan pernah dipakai di lingkungan produksi.
DUMMY_PASSWORD = "password123"


class Command(BaseCommand):
    help = (
        "Seed data awal untuk seluruh model sistem (Role, User, "
        "JabatanStrukturalMaster, Pegawai, riwayat, DataPendukung). "
        "Idempotent - aman dijalankan berkali-kali."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--minimal",
            action="store_true",
            help=(
                "Hanya seed Role + akun Admin (tanpa data dummy Staff SDM/"
                "Pegawai/riwayat). Cocok untuk lingkungan mendekati produksi."
            ),
        )

    def handle(self, *args, **options):
        self.created_counts = {}
        self.skipped_counts = {}

        with transaction.atomic():
            roles = self.seed_roles()
            self.seed_admin_user(roles)

            if options["minimal"]:
                self.stdout.write(
                    self.style.WARNING(
                        "--minimal aktif: melewati seed Staff SDM/Pegawai/riwayat."
                    )
                )
            else:
                users = self.seed_dummy_users(roles)
                jabatan_master = self.seed_jabatan_struktural_master()
                pegawai_list = self.seed_pegawai(users)
                self.seed_riwayat_studi(pegawai_list)
                self.seed_riwayat_kepangkatan(pegawai_list)
                self.seed_riwayat_jabatan_akademik(pegawai_list)
                self.seed_riwayat_jabatan_struktural(pegawai_list, jabatan_master)
                self.seed_data_pendukung(pegawai_list)

        self.print_summary()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _log(self, model_name, created):
        counts = self.created_counts if created else self.skipped_counts
        counts[model_name] = counts.get(model_name, 0) + 1

    def print_summary(self):
        self.stdout.write(self.style.SUCCESS("\n=== Ringkasan seeding ==="))
        model_names = sorted(set(self.created_counts) | set(self.skipped_counts))
        for name in model_names:
            created = self.created_counts.get(name, 0)
            skipped = self.skipped_counts.get(name, 0)
            self.stdout.write(f"{name}: {created} dibuat, {skipped} sudah ada (dilewati)")

    # ------------------------------------------------------------------
    # 1. Role
    # ------------------------------------------------------------------
    def seed_roles(self):
        roles = {}
        for nama_role in Role.NamaRole.values:
            role, created = Role.objects.get_or_create(nama_role=nama_role)
            self._log("Role", created)
            roles[nama_role] = role
        return roles

    # ------------------------------------------------------------------
    # 2. User
    # ------------------------------------------------------------------
    def seed_admin_user(self, roles):
        username = config("DJANGO_ADMIN_USERNAME", default=None)
        email = config("DJANGO_ADMIN_EMAIL", default=None)
        password = config("DJANGO_ADMIN_PASSWORD", default=None)

        if not (username and email and password):
            raise CommandError(
                "DJANGO_ADMIN_USERNAME, DJANGO_ADMIN_EMAIL, dan "
                "DJANGO_ADMIN_PASSWORD wajib diset di environment sebelum "
                "menjalankan seed_initial_data."
            )

        if User.objects.filter(username=username).exists():
            self._log("User", created=False)
            return User.objects.get(username=username)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=roles[Role.NamaRole.ADMIN],
            is_staff=True,
            is_superuser=True,
        )
        self._log("User", created=True)
        return user

    def seed_dummy_users(self, roles):
        """
        Buat akun dummy: 1 Staff SDM + beberapa Pegawai (dosen & tendik).
        Password sama untuk semua (DUMMY_PASSWORD) - HANYA development.
        """
        specs = [
            ("staff_sdm1", "staff_sdm1@hris-unimugo.local", Role.NamaRole.STAFF_SDM),
            ("dosen1", "dosen1@hris-unimugo.local", Role.NamaRole.DOSEN),
            ("dosen2", "dosen2@hris-unimugo.local", Role.NamaRole.DOSEN),
            ("tendik1", "tendik1@hris-unimugo.local", Role.NamaRole.TENDIK),
        ]

        users = {}
        for username, email, role_key in specs:
            user = User.objects.filter(username=username).first()
            created = user is None
            if created:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=DUMMY_PASSWORD,
                    role=roles[role_key],
                )
            self._log("User", created)
            users[username] = user
        return users

    # ------------------------------------------------------------------
    # 3. JabatanStrukturalMaster
    # ------------------------------------------------------------------
    def seed_jabatan_struktural_master(self):
        specs = [
            ("Rektor", 1),
            ("Dekan", 2),
            ("Kepala Departemen", 3),
        ]
        jabatan_master = {}
        for nama_jabatan, level in specs:
            jabatan, created = JabatanStrukturalMaster.objects.get_or_create(
                nama_jabatan=nama_jabatan,
                defaults={"level": level, "aktif": True},
            )
            self._log("JabatanStrukturalMaster", created)
            jabatan_master[nama_jabatan] = jabatan
        return jabatan_master

    # ------------------------------------------------------------------
    # 4. Pegawai
    # ------------------------------------------------------------------
    def seed_pegawai(self, users):
        specs = [
            (
                "dosen1",
                "0001028001",
                "Ahmad Fauzi, S.Kom., M.T.",
                Pegawai.JenisPegawai.DOSEN,
                "Fakultas Teknik",
            ),
            (
                "dosen2",
                "0002038002",
                "Siti Rahma, S.Pd., M.Pd.",
                Pegawai.JenisPegawai.DOSEN,
                "Fakultas Ilmu Pendidikan",
            ),
            (
                "tendik1",
                "199001012015031001",
                "Budi Santoso",
                Pegawai.JenisPegawai.TENDIK,
                "Biro Administrasi Umum",
            ),
        ]

        pegawai_list = []
        for username, nip_nidn, nama_lengkap, jenis_pegawai, unit_kerja in specs:
            pegawai, created = Pegawai.objects.get_or_create(
                nip_nidn=nip_nidn,
                defaults={
                    "user": users[username],
                    "nama_lengkap": nama_lengkap,
                    "jenis_pegawai": jenis_pegawai,
                    "unit_kerja": unit_kerja,
                },
            )
            self._log("Pegawai", created)
            pegawai_list.append(pegawai)
        return pegawai_list

    # ------------------------------------------------------------------
    # 5. Riwayat
    # ------------------------------------------------------------------
    def seed_riwayat_studi(self, pegawai_list):
        dosen1, dosen2, tendik1 = pegawai_list
        specs = [
            (dosen1, RiwayatStudi.Jenjang.S1, "Universitas Contoh", "S.Kom", datetime.date(2003, 8, 1)),
            (dosen1, RiwayatStudi.Jenjang.S2, "Institut Teknologi Contoh", "M.T", datetime.date(2008, 8, 1)),
            (dosen2, RiwayatStudi.Jenjang.S1, "Universitas Contoh", "S.Pd", datetime.date(2004, 8, 1)),
            (dosen2, RiwayatStudi.Jenjang.S2, "Universitas Pendidikan Contoh", "M.Pd", datetime.date(2010, 8, 1)),
            (tendik1, RiwayatStudi.Jenjang.S1, "Universitas Administrasi Contoh", "S.AP", datetime.date(2012, 8, 1)),
        ]
        for pegawai, jenjang, institusi, gelar, tahun_lulus in specs:
            _, created = RiwayatStudi.objects.get_or_create(
                pegawai=pegawai,
                jenjang=jenjang,
                tahun_lulus=tahun_lulus,
                defaults={"institusi": institusi, "gelar": gelar},
            )
            self._log("RiwayatStudi", created)

    def seed_riwayat_kepangkatan(self, pegawai_list):
        dosen1, dosen2, tendik1 = pegawai_list
        specs = [
            (dosen1, RiwayatKepangkatan.Golongan.III_B, datetime.date(2010, 1, 1)),
            (dosen1, RiwayatKepangkatan.Golongan.III_C, datetime.date(2015, 1, 1)),
            (dosen2, RiwayatKepangkatan.Golongan.III_A, datetime.date(2011, 3, 1)),
            (tendik1, RiwayatKepangkatan.Golongan.II_C, datetime.date(2015, 4, 1)),
            (tendik1, RiwayatKepangkatan.Golongan.III_A, datetime.date(2020, 4, 1)),
        ]
        for pegawai, golongan, tmt in specs:
            _, created = RiwayatKepangkatan.objects.get_or_create(
                pegawai=pegawai, golongan=golongan, tmt=tmt,
            )
            self._log("RiwayatKepangkatan", created)

    def seed_riwayat_jabatan_akademik(self, pegawai_list):
        # Jabatan akademik khusus dosen (lihat RiwayatJabatanAkademik.clean()).
        dosen1, dosen2, _tendik1 = pegawai_list
        specs = [
            (dosen1, RiwayatJabatanAkademik.Jabatan.ASISTEN_AHLI, datetime.date(2009, 1, 1)),
            (dosen1, RiwayatJabatanAkademik.Jabatan.LEKTOR, datetime.date(2016, 1, 1)),
            (dosen2, RiwayatJabatanAkademik.Jabatan.ASISTEN_AHLI, datetime.date(2012, 1, 1)),
        ]
        for pegawai, jabatan, tmt in specs:
            _, created = RiwayatJabatanAkademik.objects.get_or_create(
                pegawai=pegawai, jabatan=jabatan, tmt=tmt,
            )
            self._log("RiwayatJabatanAkademik", created)

    def seed_riwayat_jabatan_struktural(self, pegawai_list, jabatan_master):
        dosen1, dosen2, _tendik1 = pegawai_list
        specs = [
            (dosen1, jabatan_master["Kepala Departemen"], datetime.date(2020, 1, 1), None),
            (dosen2, jabatan_master["Dekan"], datetime.date(2022, 1, 1), None),
        ]
        for pegawai, jabatan, tmt, selesai in specs:
            _, created = RiwayatJabatanStruktural.objects.get_or_create(
                pegawai=pegawai, jabatan=jabatan, tmt=tmt,
                defaults={"selesai": selesai},
            )
            self._log("RiwayatJabatanStruktural", created)

    # ------------------------------------------------------------------
    # 6. DataPendukung
    # ------------------------------------------------------------------
    def seed_data_pendukung(self, pegawai_list):
        dosen1, dosen2, tendik1 = pegawai_list
        specs = [
            (
                dosen1,
                "Jl. Merdeka No. 10, Yogyakarta",
                "Rina Fauzi",
                "Istri",
                "081234500001",
                "ahmad.fauzi.alt@example.com",
                "081234500011",
            ),
            (
                dosen2,
                "Jl. Kenanga No. 5, Yogyakarta",
                "Andi Rahma",
                "Suami",
                "081234500002",
                "siti.rahma.alt@example.com",
                "081234500012",
            ),
            (
                tendik1,
                "Jl. Diponegoro No. 20, Yogyakarta",
                "Wati Santoso",
                "Istri",
                "081234500003",
                "budi.santoso.alt@example.com",
                "081234500013",
            ),
        ]
        for (
            pegawai,
            alamat,
            kontak_nama,
            kontak_hubungan,
            kontak_no_hp,
            email_kedua,
            no_hp,
        ) in specs:
            _, created = DataPendukung.objects.get_or_create(
                pegawai=pegawai,
                defaults={
                    "alamat": alamat,
                    "kontak_darurat_nama": kontak_nama,
                    "kontak_darurat_hubungan": kontak_hubungan,
                    "kontak_darurat_no_hp": kontak_no_hp,
                    "email_kedua": email_kedua,
                    "no_hp": no_hp,
                },
            )
            self._log("DataPendukung", created)
