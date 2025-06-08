from django.urls import path
from Auth import views
from Auth.views import (
    BookingCreateView,
    CustomerBookingListView,
    BookingStatusUpdateView,
    ServiceCreateView,
    ServiceUpdateView,
    AvailableServicesListView
)

urlpatterns = [
    path('signup/', views.register, name="signup"),
    path('verify-otp/', views.verify_otp, name="verify-otp"),
    path('login/', views.login, name="login"),

    path('list_services/', AvailableServicesListView.as_view(), name="all_services"),
    path('book_service/', BookingCreateView.as_view(), name='booking-service'),    
    path('my/', CustomerBookingListView.as_view(), name='booking-list'),            
    path('<uuid:pk>/', BookingStatusUpdateView.as_view(), name='booking-update'),  

    path('admin/services/', ServiceCreateView.as_view(), name='admin-service-create'),
    path('admin/services/<int:pk>/', ServiceUpdateView.as_view(), name='admin-service-update'),


    path('payment/create/', views.create_order, name="create_order"),
    path('payment/verify/', views.verify_payment, name="verify_payment"),
]