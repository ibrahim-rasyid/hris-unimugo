from rest_framework.routers import DefaultRouter

from .views import JabatanStrukturalMasterViewSet

router = DefaultRouter()
router.register(
    "jabatan-struktural-master",
    JabatanStrukturalMasterViewSet,
    basename="jabatan-struktural-master",
)

urlpatterns = router.urls
