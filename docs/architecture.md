# Arsitektur Sistem

## Stack Teknologi
- Frontend: React + React Router + Axios + React Hook Form + Zod
- Backend: Django + Django REST Framework + Simple JWT
- Database: PostgreSQL
- Deployment: Docker Compose (Django + PostgreSQL + Nginx) di satu VPS

## Alur Komunikasi
```
React (SPA)  <---- REST API (JWT) ---->  Django REST Framework
                                                |
                                          Modul RBAC (permission per role)
                                                |
                                          Modul Kepegawaian (model & business logic)
                                                |
                                          PostgreSQL
```

## Lapisan Otorisasi
1. **Autentikasi**: JWT access + refresh token (djangorestframework-simplejwt)
2. **Otorisasi berbasis role**: Django Groups/Permissions atau model Role custom
3. **Otorisasi berbasis kepemilikan**: filter queryset per request.user,
   khusus untuk endpoint DataPendukung milik Pegawai

## Keputusan Desain Kunci
- Tabel riwayat bersifat historikal (append-only), bukan snapshot -
  mendukung audit dan rekonstruksi riwayat karier pegawai kapan saja.
- Django Admin dimanfaatkan sebagai backoffice awal untuk Staff SDM,
  mempercepat MVP sebelum UI React modul SDM selesai.
- Pemisahan endpoint read (list/detail) vs write (create/update) di level
  serializer untuk kontrol akses granular.

## Setup Docker
Backend sudah di-Dockerize sebagai lingkungan development/staging (lihat
`docker-compose.yml`, `backend/Dockerfile`, `backend/entrypoint.sh`,
`nginx/conf.d/default.conf`, dan `.env.example` di root). Jalankan dengan
`cp .env.example .env` lalu `docker compose up --build`. Detail lengkap ada
di CLAUDE.md bagian "Docker (Development/Staging)". Ini bukan konfigurasi
produksi final - HTTPS via Certbot/Let's Encrypt belum diimplementasi,
hanya distrukturkan agar mudah ditambahkan belakangan.

## Fase Pengembangan (MVP)
1. Model data + Django Admin untuk CRUD dasar
2. REST API + autentikasi JWT + RBAC
3. Frontend: login, dashboard per role, form input Staff SDM
4. Modul self-service Pegawai
5. Audit log, laporan/export, validasi lanjutan