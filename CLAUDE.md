# Sistem Kepegawaian Universitas

Lihat detail lengkap di:
- docs/functional-requirements.md
- docs/architecture.md
- docs/data-model.md

## Aturan Wajib
### Tentang Proyek
Aplikasi web sistem kepegawaian untuk universitas swasta.
Stack: React (frontend) + Django REST Framework (backend) + PostgreSQL.

### Aktor dan Hak Akses

#### 1. Admin
- Setup role dan permission
- Kelola akun pengguna (aktivasi/nonaktivasi)
- TIDAK mengelola data pegawai secara langsung

#### 2. Staff SDM
- Input & kelola data induk pegawai (dosen dan tendik)
- Input & kelola riwayat studi dan gelar akademik
- Input & kelola riwayat kepangkatan/golongan
- Input & kelola riwayat jabatan akademik (khusus dosen)
- Input & kelola riwayat jabatan struktural
- Read-write penuh ke semua data pegawai KECUALI data pendukung milik pegawai

#### 3. Pegawai (Dosen/Tendik)
- Read-only untuk data induk dan semua riwayat miliknya sendiri
- Read-write HANYA untuk data pendukung miliknya sendiri:
  alamat, kontak darurat (next-of-kin), email kedua, no HP
- TIDAK BOLEH mengakses data pegawai lain

### Aturan Emas (Wajib Diikuti Setiap Generate Kode)
1. Setiap endpoint API WAJIB memvalidasi role DAN kepemilikan data
   (contoh: pegawai hanya boleh update DataPendukung dengan pegawai_id == dirinya sendiri)
2. Tabel riwayat (RiwayatStudi, RiwayatKepangkatan, RiwayatJabatanAkademik,
   RiwayatJabatanStruktural) bersifat historikal / append-only.
   JANGAN pernah overwrite record lama - selalu tambah record baru dengan tanggal (TMT).
3. Jangan generate field bebas (freeform) untuk data yang seharusnya
   pakai pilihan tetap (misalnya golongan, jenis_pegawai) - gunakan choices/enum.
4. Selalu sertakan validasi backend, jangan andalkan validasi frontend saja.

### Referensi
- Detail model data: lihat docs/data-model.md
- Detail kebutuhan fungsional: lihat docs/functional-requirements.md
- Detail arsitektur: lihat docs/architecture.md

## Konvensi Backend
### Struktur App
Setiap domain punya Django app sendiri di `backend/apps/`:
- `accounts` -> User, Role, autentikasi, permission
- `pegawai` -> data induk pegawai (dosen & tendik)
- `riwayat_studi`, `riwayat_kepangkatan`, `riwayat_jabatan_akademik`,
  `riwayat_jabatan_struktural` -> masing-masing riwayat, relasi FK ke Pegawai
- `data_pendukung` -> data self-service milik pegawai

Setiap app WAJIB punya struktur standar:
```
apps/<nama_app>/
    models.py
    serializers.py
    views.py
    permissions.py
    urls.py
    admin.py
    tests.py
```

### Model
- Gunakan `UUIDField` sebagai primary key untuk semua model utama.
- Semua tabel riwayat WAJIB punya field `tmt` (tanggal mulai tugas/berlaku)
  dan foreign key ke `Pegawai` dengan `related_name` yang jelas
  (contoh: `riwayat_kepangkatan`, bukan `riwayatkepangkatan_set`).
- Gunakan `choices=` untuk field seperti golongan, jenis_pegawai, jabatan akademik
  - jangan biarkan freeform text.
- Tambahkan `created_at`, `updated_at` di semua model (gunakan abstract base model
  `TimeStampedModel` di `apps/common/models.py` jika ada).

### Permission & Akses
- Gunakan DRF permission classes custom di `permissions.py` tiap app, JANGAN
  taruh logika role-check langsung di dalam view.
- Pola permission dasar:
  - `IsAdmin` -> hanya untuk endpoint setup role
  - `IsStaffSDM` -> untuk CRUD data pegawai & semua riwayat
  - `IsOwnerOrStaffSDM` -> untuk data pendukung (pegawai boleh edit miliknya sendiri,
    staff SDM boleh lihat semua)
- Endpoint data pendukung WAJIB filter queryset berdasarkan `request.user`,
  bukan hanya mengecek permission class saja.

### Serializer
- Pisahkan serializer untuk read vs write jika field yang bisa diubah terbatas
  (contoh: `PegawaiListSerializer` vs `PegawaiUpdateSerializer`).
- Field milik pegawai lain TIDAK BOLEH bisa diubah lewat serializer pegawai biasa.

### API Response
- Ikuti format konsisten:
  ```json
  {
    "success": true,
    "data": {},
    "message": ""
  }
  ```
- Gunakan pagination default DRF untuk semua endpoint list.

### Testing
- Setiap endpoint baru WAJIB disertai test untuk 3 skenario:
  1. Role yang berhak -> berhasil
  2. Role yang tidak berhak -> ditolak (403)
  3. Pegawai mencoba akses/ubah data pegawai lain -> ditolak (403/404)

## Docker (Development/Staging)
Backend sudah bisa dijalankan lewat Docker Compose sebagai lingkungan
development/staging yang konsisten (bukan setup produksi final - lihat
catatan HTTPS di bawah).

### File terkait
- `docker-compose.yml` (root) -> 3 service: `db` (PostgreSQL 16, dengan
  healthcheck), `backend` (Django + Gunicorn, depends_on db healthy),
  `nginx` (reverse proxy + serve `/static/` & `/media/`, port 80).
- `backend/Dockerfile` -> image `python:3.13-slim`, install dependency dari
  `backend/requirements/prod.txt` (sudah berisi `gunicorn`, `whitenoise`;
  `psycopg2-binary` ada di `requirements/base.txt`).
- `backend/entrypoint.sh` -> tunggu PostgreSQL siap (`pg_isready`), lalu
  jalankan `migrate`, `seed_initial_data`, dan `collectstatic` otomatis
  sebelum start Gunicorn.
- `backend/apps/accounts/management/commands/seed_initial_data.py` ->
  seed idempotent untuk seluruh 8 model (Role, User, JabatanStrukturalMaster,
  Pegawai, RiwayatStudi, RiwayatKepangkatan, RiwayatJabatanAkademik,
  RiwayatJabatanStruktural, DataPendukung). Akun Admin dibuat dari
  `DJANGO_ADMIN_USERNAME/EMAIL/PASSWORD` (env, wajib diisi); akun Staff SDM
  & Pegawai dummy pakai password contoh `password123` (JANGAN dipakai di
  produksi). Jalankan dengan `--minimal` untuk hanya seed Role + Admin
  tanpa data dummy lain (cocok untuk lingkungan mendekati produksi).
- `backend/.dockerignore` -> exclude `venv/`, `__pycache__/`, `.env`, dll.
- `nginx/conf.d/default.conf` -> reverse proxy ke `backend:8000`, serve
  static/media langsung dari named volume, sudah ada catatan cara
  menambahkan HTTPS via Certbot/Let's Encrypt nanti (belum diimplementasi).
- `.env.example` (root) -> template environment variable untuk Compose
  (SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB_*, CORS_ALLOWED_ORIGINS, dst).
  Beda dari `backend/.env.example` yang dipakai untuk dev non-Docker.

### Cara menjalankan
```bash
cp .env.example .env   # isi dengan nilai asli, JANGAN commit .env
docker compose up --build
```
API akan bisa diakses lewat Nginx di `http://localhost/` (contoh:
`http://localhost/api/auth/token/`, `http://localhost/admin/`).

### Catatan penting
- Container backend selalu jalan dengan `DJANGO_SETTINGS_MODULE=config.settings.prod`,
  yang sudah hardcode `DEBUG = False` terlepas dari isi env var.
- `CORS_ALLOWED_ORIGINS` dan `SECRET_KEY` WAJIB diisi lewat `.env` - tidak
  ada wildcard `*` dan tidak ada nilai hardcode di kode.
- HTTPS belum diimplementasi penuh; struktur `docker-compose.yml` dan
  `nginx/conf.d/default.conf` sudah disiapkan (volume & komentar) supaya
  Certbot/Let's Encrypt bisa ditambahkan tanpa restrukturisasi besar.

## Konvensi Frontend
### Struktur Folder
- `src/features/` dipecah PER ROLE, bukan per jenis komponen:
  - `auth` -> login, logout, guard route
  - `admin-role` -> setup role & permission (khusus Admin)
  - `sdm-pegawai` -> input/kelola data induk pegawai (khusus Staff SDM)
  - `sdm-riwayat` -> input/kelola semua riwayat (khusus Staff SDM)
  - `pegawai-self-service` -> update data pendukung & lihat data pribadi (khusus Pegawai)
- `src/components/common/` -> komponen generik dipakai lintas role (Button, Table, Modal)
- `src/components/forms/` -> komponen form generik (InputField, DatePicker, SelectField)
- `src/api/` -> semua fungsi pemanggilan API, dikelompokkan per resource
  (contoh: `api/pegawai.js`, `api/riwayatKepangkatan.js`)
- `src/context/` -> AuthContext (menyimpan user & role aktif)

### Routing & Proteksi Akses
- Gunakan komponen `<ProtectedRoute allowedRoles={[...]}>` untuk membatasi
  akses halaman berdasarkan role dari AuthContext.
- JANGAN hanya menyembunyikan tombol/menu di UI sebagai satu-satunya proteksi -
  backend tetap menjadi sumber kebenaran otorisasi.

### State Management
- Gunakan Context API + hooks untuk state global (auth, role).
- Untuk state form, gunakan React Hook Form.
- Untuk validasi form, gunakan Zod, definisikan schema di file terpisah
  `*.schema.js` di folder feature masing-masing.

### Komunikasi API
- Semua request lewat instance Axios tunggal di `src/api/axiosInstance.js`
  dengan interceptor untuk menyisipkan token JWT dan menangani 401
  (redirect ke login).
- Jangan panggil `fetch`/`axios` langsung di dalam komponen - selalu lewat
  fungsi di `src/api/`.

### Penamaan
- Komponen: PascalCase (`RiwayatKepangkatanForm.jsx`)
- Hook custom: camelCase dengan prefix `use` (`usePegawaiData.js`)
- File API: camelCase sesuai resource (`riwayatKepangkatan.js`)

### Form Data Pendukung (Self-Service)
- Form ini HANYA boleh menampilkan field yang memang bisa diubah pegawai:
  alamat, kontak darurat, email kedua, no HP.
- Field data induk/riwayat ditampilkan read-only di halaman terpisah
  ("Data Pribadi"), tidak dicampur dengan form edit.

## Batasan Environment
Claude Code TIDAK memiliki akses ke virtual environment (venv) proyek ini.
JANGAN PERNAH mencoba menjalankan `python manage.py` (migrate, test, runserver,
dll) - selalu tulis/edit kode saja, dan beri tahu perintah apa yang PERLU
dijalankan pengguna secara manual di akhir respons.