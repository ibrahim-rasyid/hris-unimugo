---
description: Konvensi kode frontend React - berlaku untuk file di folder frontend/
globs: frontend/**/*.{js,jsx,ts,tsx}
alwaysApply: false
---

# Konvensi Frontend (React)

## Struktur Folder
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

## Routing & Proteksi Akses
- Gunakan komponen `<ProtectedRoute allowedRoles={[...]}>` untuk membatasi
  akses halaman berdasarkan role dari AuthContext.
- JANGAN hanya menyembunyikan tombol/menu di UI sebagai satu-satunya proteksi -
  backend tetap menjadi sumber kebenaran otorisasi.

## State Management
- Gunakan Context API + hooks untuk state global (auth, role).
- Untuk state form, gunakan React Hook Form.
- Untuk validasi form, gunakan Zod, definisikan schema di file terpisah
  `*.schema.js` di folder feature masing-masing.

## Komunikasi API
- Semua request lewat instance Axios tunggal di `src/api/axiosInstance.js`
  dengan interceptor untuk menyisipkan token JWT dan menangani 401
  (redirect ke login).
- Jangan panggil `fetch`/`axios` langsung di dalam komponen - selalu lewat
  fungsi di `src/api/`.

## Penamaan
- Komponen: PascalCase (`RiwayatKepangkatanForm.jsx`)
- Hook custom: camelCase dengan prefix `use` (`usePegawaiData.js`)
- File API: camelCase sesuai resource (`riwayatKepangkatan.js`)

## Form Data Pendukung (Self-Service)
- Form ini HANYA boleh menampilkan field yang memang bisa diubah pegawai:
  alamat, kontak darurat, email kedua, no HP.
- Field data induk/riwayat ditampilkan read-only di halaman terpisah
  ("Data Pribadi"), tidak dicampur dengan form edit.
