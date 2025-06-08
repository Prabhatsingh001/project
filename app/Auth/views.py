from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAdminUser
from rest_framework.response import Response
from rest_framework import status,generics, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied


from .models import Booking,CustomUser,Service,ProviderProfile
from .serializers import SignUpserializer, LoginSerializer, OTPVerifySerializer,BookingSerializer,ServiceSerializerAdmin, ServiceSerializer
from .otp_service import send_mock_otp, verify_mock_otp
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib




@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = SignUpserializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        email = user.email
        send_mock_otp(email)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    serializer = OTPVerifySerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email'] #type: ignore
        otp = serializer.validated_data['otp'] #type: ignore
        if verify_mock_otp(email, otp):
            try:
                user = CustomUser.objects.get(email=email)
                user.is_verified = True
                user.save()
                return Response({"message": "OTP verified successfully"})
            except CustomUser.DoesNotExist:
                return Response({"error": "User does not exist"}, status = status.HTTP_404_NOT_FOUND)
        return Response({"error": "Invalid OTP"}, status = status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email'] #type: ignore
        password = serializer.validated_data['password'] #type: ignore
        try:
            user = CustomUser.objects.get(email=email)
            if not user.is_verified:
                return Response({"error": "User not verified"}, status=status.HTTP_401_UNAUTHORIZED)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                "success": True,
                "message": "Login successful",
                "data": {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
                },
                },status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvailableServicesListView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  #type: ignore
        return Service.objects.all()



class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'customer_profile'):
            raise PermissionDenied("Only customers can create bookings.")
        serializer.save(customer=user.customer_profile) #type: ignore




class CustomerBookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  #type: ignore
        user = self.request.user
        if hasattr(user, 'customer_profile'):
            return Booking.objects.filter(customer=user.customer_profile)  #type: ignore
        return Booking.objects.none()


class ProviderBookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  #type: ignore
        user = self.request.user
        try:
            provider_profile = user.provider_profile  #type: ignore
        except ProviderProfile.DoesNotExist:
            return Booking.objects.none()
        return Booking.objects.filter(service__provider=provider_profile)


class BookingStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            provider_profile = request.user.provider_profile
        except ProviderProfile.DoesNotExist:
            raise PermissionDenied("You are not authorized to update this booking.")

        if booking.service.provider != provider_profile:
            raise PermissionDenied("You are not authorized to update this booking.")

        new_status = request.data.get('status')
        if new_status not in dict(Booking.STATUS_CHOICES):
            return Response({"error": "Invalid status"}, status=400)

        booking.status = new_status
        booking.save()
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)


#admin views

class ServiceCreateView(generics.CreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializerAdmin
    permission_classes = [IsAdminUser]


class ServiceUpdateView(generics.RetrieveUpdateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializerAdmin
    permission_classes = [IsAdminUser]




#payment services

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@api_view(['POST'])
def create_order(request):
    amount = request.data.get('amount')  # Amount in INR
    if not amount:
        return Response({'error': 'Amount is required'}, status=400)

    amount_paise = int(float(amount) * 100)  # Razorpay uses paise
    order_data = {
        'amount': amount_paise,
        'currency': 'INR',
        'payment_capture': '1',
    }

    try:
        razorpay_order = razorpay_client.order.create(data=order_data)  #type: ignore
        return Response({ 
            'order_id': razorpay_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': amount_paise,
            'currency': 'INR'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['POST'])
def verify_payment(request):
    data = request.data
    try:
        order_id = data['razorpay_order_id']
        payment_id = data['razorpay_payment_id']
        signature = data['razorpay_signature']

        body = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            bytes(settings.RAZORPAY_KEY_SECRET, 'utf-8'),
            bytes(body, 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        if expected_signature == signature:
            return Response({'status': 'Payment verified successfully'})
        else:
            return Response({'error': 'Signature mismatch'}, status=400)
    except KeyError:
        return Response({'error': 'Invalid data'}, status=400)
