from rest_framework import serializers

from .models import Role, User


class RoleMiniSerializer(serializers.ModelSerializer):
    """
    Representasi ringkas Role, dipakai sebagai nested field
    (bukan endpoint utama pengelolaan role - itu ada di viewset terpisah
    untuk ADM-01/ADM-02).
    """

    class Meta:
        model = Role
        fields = ["id", "nama_role"]
        read_only_fields = fields


class UserMiniSerializer(serializers.ModelSerializer):
    """
    Representasi ringkas User + role-nya, dipakai sebagai nested field
    di PegawaiListSerializer. Tidak menyertakan field sensitif
    (password, is_staff, is_superuser, dll).
    """

    role = RoleMiniSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "role"]
        read_only_fields = fields