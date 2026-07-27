---
description: Ringkasan proyek Sistem Kepegawaian - selalu jadi konteks utama
alwaysApply: true
---

# Sistem Kepegawaian Universitas

## Tentang Proyek
Aplikasi web sistem kepegawaian untuk universitas swasta.
Stack: React (frontend) + Django REST Framework (backend) + PostgreSQL.

## Aktor dan Hak Akses

### 1. Admin
- Setup role dan permission
- Kelola akun pengguna (aktivasi/nonaktivasi)
- TIDAK mengelola data pegawai secara langsung

### 2. Staff SDM
- Input & kelola data induk pegawai (dosen dan tendik)
- Input & kelola riwayat studi dan gelar akademik
- Input & kelola riwayat kepangkatan/golongan
- Input & kelola riwayat jabatan akademik (khusus dosen)
- Input & kelola riwayat jabatan struktural
- Read-write penuh ke semua data pegawai KECUALI data pendukung milik pegawai

### 3. Pegawai (Dosen/Tendik)
- Read-only untuk data induk dan semua riwayat miliknya sendiri
- Read-write HANYA untuk data pendukung miliknya sendiri:
  alamat, kontak darurat (next-of-kin), email kedua, no HP
- TIDAK BOLEH mengakses data pegawai lain

## Aturan Emas (Wajib Diikuti Setiap Generate Kode)
1. Setiap endpoint API WAJIB memvalidasi role DAN kepemilikan data
   (contoh: pegawai hanya boleh update DataPendukung dengan pegawai_id == dirinya sendiri)
2. Tabel riwayat (RiwayatStudi, RiwayatKepangkatan, RiwayatJabatanAkademik,
   RiwayatJabatanStruktural) bersifat historikal / append-only.
   JANGAN pernah overwrite record lama - selalu tambah record baru dengan tanggal (TMT).
3. Jangan generate field bebas (freeform) untuk data yang seharusnya
   pakai pilihan tetap (misalnya golongan, jenis_pegawai) - gunakan choices/enum.
4. Selalu sertakan validasi backend, jangan andalkan validasi frontend saja.

## Referensi
- Detail model data: lihat docs/data-model.md
- Detail kebutuhan fungsional: lihat docs/functional-requirements.md
- Detail arsitektur: lihat docs/architecture.md
