from __future__ import annotations

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from users.models import Address, DriverProfile, User, VehicleType


class OtpRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()


class OtpVerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()


class OtpRequestResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    otp = serializers.CharField()


class OtpVerifyResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class BlacklistRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        refresh = attrs.get("refresh")
        try:
            token = RefreshToken(refresh)  # type: ignore[arg-type]
            token.blacklist()
        except TokenError as exc:
            raise serializers.ValidationError({"refresh": "Invalid or expired token."}) from exc
        return attrs


class CustomerProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    age = serializers.IntegerField(required=False, allow_null=True)

    def validate_phone(self, value: str) -> str:
        user = self.context["request"].user
        if User.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value


class SellerProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    age = serializers.IntegerField(required=False, allow_null=True)

    def validate_phone(self, value: str) -> str:
        user = self.context["request"].user
        if User.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value


class BasicProfileResponseSerializer(serializers.Serializer):
    name = serializers.CharField()
    phone = serializers.CharField()
    age = serializers.IntegerField(allow_null=True)


class DriverProfileSerializer(serializers.ModelSerializer):
    """Serializer for driver profile details."""
    email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)
    name = serializers.CharField(source="user.name", read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    age = serializers.IntegerField(source="user.age", read_only=True)
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = DriverProfile
        fields = [
            "id",
            "email",
            "name",
            "phone",
            "age",
            "roles",
            "status",
            "vehicle_type",
            "accepts_food",
            "accepts_shipping",
            "accepts_taxi",
            "is_online",
            "driving_license",
            "id_document",
            "other_documents",
            "created_at",
        ]

    def get_roles(self, obj: DriverProfile) -> list[str]:
        return list(obj.user.roles.values_list("name", flat=True))


class DriverProfileUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    age = serializers.IntegerField(required=False, allow_null=True)
    vehicle_type = serializers.ChoiceField(choices=VehicleType.choices, required=False)
    accepts_food = serializers.BooleanField(required=False)
    accepts_shipping = serializers.BooleanField(required=False)
    accepts_taxi = serializers.BooleanField(required=False)
    driving_license = serializers.FileField(required=False, allow_null=True)
    id_document = serializers.FileField(required=False, allow_null=True)
    other_documents = serializers.FileField(required=False, allow_null=True)

    def validate_phone(self, value: str) -> str:
        user = self.context["request"].user
        if User.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "lat",
            "lng",
            "full_address",
            "street_name",
            "house_number",
            "city",
            "postal_code",
            "country",
            "created_at",
        ]


class AddressCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "label",
            "lat",
            "lng",
            "full_address",
            "street_name",
            "house_number",
            "city",
            "postal_code",
            "country",
        ]


class UserMeSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "phone",
            "age",
            "is_verified",
            "created_at",
            "roles",
        ]

    def get_roles(self, obj: User) -> list[str]:
        return list(obj.roles.values_list("name", flat=True))


class UserMeUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    age = serializers.IntegerField(required=False, allow_null=True)

    def validate_phone(self, value: str) -> str:
        user = self.context["request"].user
        if User.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value
