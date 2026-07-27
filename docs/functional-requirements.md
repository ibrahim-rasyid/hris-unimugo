# Kebutuhan Fungsional - Sistem Kepegawaian Universitas

## Aktor
1. Admin
2. Staff SDM
3. Pegawai (Dosen / Tendik)

## Admin
| Kode | Fungsi | Deskripsi |
|------|--------|-----------|
| ADM-01 | Setup role | Membuat, mengubah, menghapus role |
| ADM-02 | Setup permission | Mengatur hak akses tiap role terhadap modul |
| ADM-03 | Kelola akun | Aktivasi/nonaktivasi akun pengguna, reset password |
| ADM-04 | Audit log | Melihat log aktivitas penting di sistem |
| ADM-05 | Setup master jabatan struktural | Membuat, mengubah, menghapus jabatan struktural yang tersedia |

## Staff SDM
| Kode | Fungsi | Deskripsi |
|------|--------|-----------|
| SDM-01 | Input data pegawai | CRUD data induk dosen dan tendik |
| SDM-02 | Input riwayat studi | CRUD riwayat pendidikan dan gelar akademik |
| SDM-03 | Input riwayat kepangkatan | CRUD riwayat golongan/kepangkatan |
| SDM-04 | Input jabatan akademik | CRUD riwayat jabatan akademik (khusus dosen) |
| SDM-05 | Input jabatan struktural | CRUD riwayat jabatan struktural |
| SDM-06 | Laporan | Generate rekap data kepegawaian |

## Pegawai
| Kode | Fungsi | Deskripsi |
|------|--------|-----------|
| PEG-01 | Lihat data pribadi | Melihat data induk & seluruh riwayat miliknya (read-only) |
| PEG-02 | Update data pendukung | Mengubah alamat, kontak darurat, email kedua, no HP |

## Kebutuhan Non-Fungsional
- Keamanan: HTTPS wajib, password hashing, rate limiting login
- Privasi: kepatuhan terhadap UU PDP untuk data pribadi pegawai
- Auditability: setiap perubahan data riwayat tercatat (siapa, kapan, apa)
- Skalabilitas: cukup untuk skala 1 universitas (ratusan-ribuan pegawai),
  tidak perlu arsitektur microservices
