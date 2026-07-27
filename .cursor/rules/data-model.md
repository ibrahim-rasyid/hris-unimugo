---
description: Ringkasan model data / ERD - jadi rujukan saat generate model, serializer, atau form
globs: backend/apps/**/models.py
alwaysApply: false
---

# Ringkasan Model Data

## Entitas Utama & Relasi

```
User (1) ---- (1) Pegawai
User (N) ---- (1) Role
Pegawai (1) ---- (N) RiwayatStudi
Pegawai (1) ---- (N) RiwayatKepangkatan
Pegawai (1) ---- (N) RiwayatJabatanAkademik
Pegawai (1) ---- (N) RiwayatJabatanStruktural
Pegawai (1) ---- (1) DataPendukung
```

## Field Kunci Tiap Entitas

**User**
- id (UUID, PK), username, password_hash, role_id (FK)

**Role**
- id (UUID, PK), nama_role (choices: admin, staff_sdm, dosen, tendik)

**Pegawai**
- id (UUID, PK), user_id (FK), nip_nidn, nama_lengkap,
  jenis_pegawai (choices: dosen, tendik), unit_kerja

**RiwayatStudi**
- id (UUID, PK), pegawai_id (FK), jenjang (choices: S1, S2, S3),
  institusi, gelar, tahun_lulus

**RiwayatKepangkatan**
- id (UUID, PK), pegawai_id (FK), golongan (choices), tmt (tanggal)

**RiwayatJabatanAkademik** (khusus dosen)
- id (UUID, PK), pegawai_id (FK),
  jabatan (choices: asisten_ahli, lektor, lektor_kepala, guru_besar), tmt

**RiwayatJabatanStruktural**
- id (UUID, PK), pegawai_id (FK), jabatan (contoh: kaprodi, dekan, kabiro),
  tmt (tanggal mulai), selesai (tanggal selesai, nullable jika masih menjabat)

**DataPendukung**
- id (UUID, PK), pegawai_id (FK, unique - relasi 1-1),
  alamat, kontak_darurat, email_kedua, no_hp

## Aturan Penting
- Semua tabel riwayat bersifat APPEND-ONLY. Perubahan pangkat/jabatan baru
  = record baru, bukan update record lama.
- `DataPendukung` adalah SATU-SATUNYA tabel yang boleh diubah oleh role Pegawai.
- Relasi `Pegawai -> User` adalah 1-1, dan `User -> Role` adalah N-1
  (banyak user bisa punya role yang sama, tapi satu user cuma satu role).
