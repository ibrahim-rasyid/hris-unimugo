from rest_framework.routers import DefaultRouter

from .views import RiwayatStudiViewSet

router = DefaultRouter()
router.register("riwayat-studi", RiwayatStudiViewSet, basename="riwayat-studi")

urlpatterns = router.urls
