from rest_framework.routers import DefaultRouter

from .views import RiwayatKepangkatanViewSet

router = DefaultRouter()
router.register(
    "riwayat-kepangkatan", RiwayatKepangkatanViewSet, basename="riwayat-kepangkatan"
)

urlpatterns = router.urls
