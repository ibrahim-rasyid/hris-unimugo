---
description: Konvensi kode backend Django - berlaku untuk file di folder backend/
globs: backend/**/*.py
alwaysApply: false
---

# Konvensi Backend (Django + DRF)

## Struktur App
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

## Model
- Gunakan `UUIDField` sebagai primary key untuk semua model utama.
- Semua tabel riwayat WAJIB punya field `tmt` (tanggal mulai tugas/berlaku)
  dan foreign key ke `Pegawai` dengan `related_name` yang jelas
  (contoh: `riwayat_kepangkatan`, bukan `riwayatkepangkatan_set`).
- Gunakan `choices=` untuk field seperti golongan, jenis_pegawai, jabatan akademik
  - jangan biarkan freeform text.
- Tambahkan `created_at`, `updated_at` di semua model (gunakan abstract base model
  `TimeStampedModel` di `apps/common/models.py` jika ada).

## Permission & Akses
- Gunakan DRF permission classes custom di `permissions.py` tiap app, JANGAN
  taruh logika role-check langsung di dalam view.
- Pola permission dasar:
  - `IsAdmin` -> hanya untuk endpoint setup role
  - `IsStaffSDM` -> untuk CRUD data pegawai & semua riwayat
  - `IsOwnerOrStaffSDM` -> untuk data pendukung (pegawai boleh edit miliknya sendiri,
    staff SDM boleh lihat semua)
- Endpoint data pendukung WAJIB filter queryset berdasarkan `request.user`,
  bukan hanya mengecek permission class saja.

## Serializer
- Pisahkan serializer untuk read vs write jika field yang bisa diubah terbatas
  (contoh: `PegawaiListSerializer` vs `PegawaiUpdateSerializer`).
- Field milik pegawai lain TIDAK BOLEH bisa diubah lewat serializer pegawai biasa.

## API Response
- Ikuti format konsisten:
  ```json
  {
    "success": true,
    "data": {},
    "message": ""
  }
  ```
- Gunakan pagination default DRF untuk semua endpoint list.

## Testing
- Setiap endpoint baru WAJIB disertai test untuk 3 skenario:
  1. Role yang berhak -> berhasil
  2. Role yang tidak berhak -> ditolak (403)
  3. Pegawai mencoba akses/ubah data pegawai lain -> ditolak (403/404)
