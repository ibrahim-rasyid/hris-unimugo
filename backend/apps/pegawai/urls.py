from rest_framework.routers import DefaultRouter

from .views import PegawaiViewSet

router = DefaultRouter()
router.register("pegawai", PegawaiViewSet, basename="pegawai")

urlpatterns = router.urls