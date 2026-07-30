from rest_framework.routers import DefaultRouter

from .views import RiwayatJabatanAkademikViewSet

router = DefaultRouter()
router.register(
    "riwayat-jabatan-akademik",
    RiwayatJabatanAkademikViewSet,
    basename="riwayat-jabatan-akademik",
)

urlpatterns = router.urls
