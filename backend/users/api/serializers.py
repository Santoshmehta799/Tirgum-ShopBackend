from cart.models import Cart
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    cart_id = serializers.SerializerMethodField()
    class Meta:
        model = User
        extra_kwargs = {
            'password': {'write_only': True}
        }
        read_only_fields = ("is_active", "is_approved", "user_type")
        exclude = (
        "groups", "user_permissions", "user_type", "first_name", "last_name", "is_staff", "is_superuser", "username")


    def get_cart_id(self, obj):
        try:
            cart = Cart.objects.filter(user=obj).first()
            if cart:
                return cart.id
            return None
        except Exception:
            return None

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(raw_password=validated_data.get('password'))
        user.save()
        return user

    def update(self, instance, validated_data):
        validated_data.pop("password", None)
        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(
        label=_("Email"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'),
                                email=email, password=password)

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user is registered with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    new_password = serializers.CharField()



# NIP SERIALIZER

# class NIPLookupSerializer(serializers.Serializer):
#     """
#     Serializer for NIP lookup results
#     """
#     name = serializers.CharField(max_length=255)
#     regon = serializers.CharField(max_length=14)
#     nip = serializers.CharField(max_length=10)
#     address = serializers.CharField(max_length=255)
#     type = serializers.CharField(max_length=20)
#     voivodeship = serializers.CharField(max_length=100)
#     city = serializers.CharField(max_length=100)
#     postal_code = serializers.CharField(max_length=10)
#     street = serializers.CharField(max_length=100)
#     building_number = serializers.CharField(max_length=20)
#     apartment_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
#     status = serializers.CharField(max_length=20)
#     raw_data = serializers.DictField(required=False)  # Optional raw data field

# class NIPLookupRequestSerializer(serializers.Serializer):
#     """
#     Serializer for NIP lookup request validation
#     """
#     nip = serializers.CharField(max_length=10, required=True)
    
#     def validate_nip(self, value):
#         """
#         Validate that NIP is in the correct format
#         """
#         # Basic NIP validation - 10 digits
#         if not value.isdigit() or len(value) != 10:
#             raise serializers.ValidationError("NIP must be exactly 10 digits")
#         return value
