from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, CreateOrderLogView, DashboardStatsView, HeroSlideViewSet, admin_login



router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'heroslides', HeroSlideViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('login/', admin_login, name='admin-login'),

    path('log-order/', CreateOrderLogView.as_view(), name='log-order'),
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]

