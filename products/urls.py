from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet, CreateOrderLogView,
    DashboardStatsView, HeroSlideViewSet, HomePageView,
    TrackVisitView, VisitorListView, admin_login, ping, verify_token,
    CloudinarySignatureView, UploadImageView, ClearVisitorsView
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'heroslides', HeroSlideViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('ping/', ping, name='ping'),
    path('login/', admin_login, name='admin-login'),
    path('verify-token/', verify_token, name='verify-token'),
    path('homepage/', HomePageView.as_view(), name='homepage'),
    path('log-order/', CreateOrderLogView.as_view(), name='log-order'),
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('track-visit/', TrackVisitView.as_view(), name='track-visit'),
    path('visitors/', VisitorListView.as_view(), name='visitor-list'),
    path('cloudinary-signature/', CloudinarySignatureView.as_view(), name='cloudinary-signature'),
    path('upload-image/', UploadImageView.as_view(), name='upload-image'),
    path('clear-visitors/', ClearVisitorsView.as_view(), name='clear-visitors'),
]
