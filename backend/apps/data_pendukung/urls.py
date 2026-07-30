from rest_framework.routers import DefaultRouter

from .views import DataPendukungViewSet

router = DefaultRouter()
router.register(
    "data-pendukung", DataPendukungViewSet, basename="data-pendukung"
)

urlpatterns = router.urls
