from rest_framework import permissions, viewsets

from apps.accounts.permissions import IsAdmin

from .models import JabatanStrukturalMaster
from .serializers import JabatanStrukturalMasterSerializer


class JabatanStrukturalMasterViewSet(viewsets.ModelViewSet):
    """
    Endpoint data master jabatan struktural (ADM-05).

    Berbeda dari tabel riwayat lain, data ini bersifat konfigurasi/
    referensi (bukan historikal), sehingga full CRUD (termasuk delete)
    diaktifkan.

    Aturan akses:
    - list/retrieve: semua user login (termasuk Staff SDM) boleh baca,
      dipakai untuk populate dropdown pilihan jabatan saat input riwayat
      jabatan struktural.
    - create/update/partial_update/destroy: hanya Admin (ADM-05).
    """

    serializer_class = JabatanStrukturalMasterSerializer
    queryset = JabatanStrukturalMaster.objects.all()

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
        ):
            return [permissions.IsAuthenticated(), IsAdmin()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()

        aktif = self.request.query_params.get("aktif")
        if aktif is not None:
            aktif_bool = aktif.lower() in ("true", "1")
            qs = qs.filter(aktif=aktif_bool)

        return qs
