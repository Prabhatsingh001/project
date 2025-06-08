from rest_framework import serializers
from django.core.validators import EmailValidator
from .models import Booking,CustomUser,Service,ProviderProfile


class SignUpserializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=True, min_length=8)
    # email_otp = serializers.CharField(write_only=True, required=True)
    # phone_otp = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'phone_number', 'password', 'password2','is_provider', 'is_verified', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
            'phone_number': {'required': True, 'allow_blank': False},
            'password': {'write_only': True, 'min_length': 8},
        }

        
    def validate(self, attrs):
        """
        checks if both passowrds match
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
            
        try:
            EmailValidator()(attrs['email'])
        except serializers.ValidationError:
            raise serializers.ValidationError({"email": "Invalid email address."})
            
        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
            
        if CustomUser.objects.filter(phone_number=attrs['phone_number']).exists():
            raise serializers.ValidationError({"phone_number": "Phone number already exists."})
        return attrs
    
    def create(self, validated_data):
        """
        creates a new user
        """
        validated_data.pop('password2')
        user = CustomUser(
            email = validated_data['email'],
            phone_number = validated_data['phone_number'],
            is_provider = validated_data['is_provider'],
            is_verified = validated_data.get('is_verified', False)
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        try:
            user = CustomUser.objects.get(email=attrs['email'])
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User not found")

        if not user.is_verified:
            raise serializers.ValidationError("User not verified")

        if not user.check_password(attrs['password']):
            raise serializers.ValidationError("Invalid credentials")

        attrs['user'] = user
        return attrs
    

class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderProfile
        fields = ['first_name', 'last_name', 'address']


class ServiceSerializer(serializers.ModelSerializer):
    provider = ProviderSerializer(read_only=True)

    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'provider']



class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'customer', 'service', 'schedule', 'status']
        read_only_fields = ['id', 'customer', 'status']


#for admin
class ServiceSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'price', 'provider']
