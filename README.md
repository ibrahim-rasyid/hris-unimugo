# Sistem Kepegawaian Universitas

Aplikasi web sistem kepegawaian berbasis React (frontend) dan Django (backend).

## Struktur Proyek
```
sistem-kepegawaian/
├── backend/          # Django REST API
├── frontend/         # React SPA
├── docs/             # Dokumen rancangan (requirement, ERD, arsitektur)
└── .cursor/rules/    # Konteks proyek untuk Cursor AI
```

## Sebelum Mulai Coding
1. Baca `docs/functional-requirements.md` untuk kebutuhan fungsional lengkap
2. Baca `docs/architecture.md` untuk gambaran arsitektur
3. File di `.cursor/rules/` akan otomatis jadi konteks saat menggunakan Cursor -
   tidak perlu dijelaskan ulang di setiap prompt

## Setup Backend (Django)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # atau venv\Scripts\activate di Windows
pip install -r requirements/dev.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Setup Frontend (React)
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Aktor Sistem
- **Admin**: setup role & permission
- **Staff SDM**: kelola data pegawai dan seluruh riwayat karier
- **Pegawai**: lihat data pribadi, update data pendukung (alamat, kontak darurat, dll)
