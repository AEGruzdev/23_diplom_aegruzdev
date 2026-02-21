from django.urls import path, include
from . import views

urlpatterns = [
    # Аутентификация
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    
    # Профиль пользователя
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Контакты пользователя
    path('contacts/', views.ContactListCreateView.as_view(), name='contact-list'),
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='contact-detail'),
    
    # Товары
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:product_id>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    # Корзина
    path('cart/', views.CartView.as_view(), name='cart'),
    
    # Заказы
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<int:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/confirm/', views.OrderConfirmView.as_view(), name='order-confirm'),
    
    # Поставщики
    path('supplier/orders/', views.SupplierOrderListView.as_view(), name='supplier-order-list'),
    path('supplier/orders/<int:order_id>/', views.SupplierOrderDetailView.as_view(), 
         name='supplier-order-detail'),
    path('supplier/shop/', views.ShopUpdateView.as_view(), name='supplier-shop'),
]