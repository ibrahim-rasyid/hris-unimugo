from rest_framework.routers import DefaultRouter

from .views import RiwayatJabatanStrukturalViewSet

router = DefaultRouter()
router.register(
    "riwayat-jabatan-struktural",
    RiwayatJabatanStrukturalViewSet,
    basename="riwayat-jabatan-struktural",
)

urlpatterns = router.urls
