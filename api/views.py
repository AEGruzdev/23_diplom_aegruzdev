from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import *
from .serializers import *
from .utils.auth_utils import IsOwnerOrReadOnly


class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    """Профиль пользователя"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ContactListCreateView(generics.ListCreateAPIView):
    """Список контактов и создание нового контакта"""
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детали контакта, обновление, удаление"""
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Переопределяем метод для возврата 204"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductListView(generics.ListAPIView):
    """Список товаров с фильтрацией"""
    serializer_class = ProductInfoSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = ProductInfo.objects.filter(quantity__gt=0, shop__state=True)
        
        # Фильтрация по категории
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        
        # Фильтрация по магазину
        shop_id = self.request.query_params.get('shop')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        
        # Поиск по названию
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(product__name__icontains=search) | 
                Q(name__icontains=search)
            )
        
        # Сортировка
        ordering = self.request.query_params.get('ordering', 'price')
        if ordering in ['price', '-price', 'name', '-name']:
            queryset = queryset.order_by(ordering)
        
        return queryset.distinct()


class ProductDetailView(generics.RetrieveAPIView):
    """Детальная информация о товаре"""
    queryset = ProductInfo.objects.filter(quantity__gt=0)
    serializer_class = ProductInfoSerializer
    permission_classes = [permissions.AllowAny]
    lookup_url_kwarg = 'product_id'


class CartView(APIView):
    """Работа с корзиной"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Получение корзины пользователя"""
        cart, _ = Order.objects.get_or_create(
            user=request.user,
            status='basket'
        )
        serializer = OrderSerializer(cart)
        return Response(serializer.data)
    
    @transaction.atomic
    def post(self, request):
        """Добавление товара в корзину"""
        cart, _ = Order.objects.get_or_create(
            user=request.user,
            status='basket'
        )
        
        serializer = OrderItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            product_info = serializer.validated_data['product_info']
            
            # Проверяем, есть ли уже такой товар в корзине
            item, created = OrderItem.objects.get_or_create(
                order=cart,
                product_info=product_info,
                defaults={
                    'shop': product_info.shop,
                    'quantity': serializer.validated_data['quantity']
                }
            )
            
            if not created:
                # Если товар уже есть, увеличиваем количество
                new_quantity = item.quantity + serializer.validated_data['quantity']
                if new_quantity > product_info.quantity:
                    return Response(
                        {'error': f'Доступно только {product_info.quantity} шт.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                item.quantity = new_quantity
                item.save()
            
            return Response(OrderSerializer(cart).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @transaction.atomic
    def delete(self, request):
        """Удаление товара из корзины"""
        cart = get_object_or_404(Order, user=request.user, status='basket')
        item_id = request.data.get('item_id')
        
        if not item_id:
            return Response(
                {'error': 'Не указан item_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = cart.items.get(id=item_id)
            item.delete()
            # Возвращаем 204 No Content
            return Response(status=status.HTTP_204_NO_CONTENT)
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Товар не найден в корзине'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @transaction.atomic
    def put(self, request):
        """Обновление количества товара в корзине"""
        cart = get_object_or_404(Order, user=request.user, status='basket')
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        if not item_id or not quantity:
            return Response(
                {'error': 'Не указаны item_id или quantity'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = cart.items.get(id=item_id)
            if quantity > item.product_info.quantity:
                return Response(
                    {'error': f'Доступно только {item.product_info.quantity} шт.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item.quantity = quantity
            item.save()
            return Response(OrderSerializer(cart).data)
        
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Товар не найден в корзине'},
                status=status.HTTP_404_NOT_FOUND
            )


class OrderConfirmView(APIView):
    """Подтверждение заказа"""
    permission_classes = [permissions.IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        cart = get_object_or_404(Order, user=request.user, status='basket')
        
        serializer = OrderConfirmSerializer(data=request.data)
        if serializer.is_valid():
            contact = get_object_or_404(Contact, id=serializer.validated_data['contact_id'])
            
            if cart.items.count() == 0:
                return Response(
                    {'error': 'Корзина пуста'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Подтверждаем заказ
            cart.status = 'new'
            cart.contact = contact
            cart.save()
            
            # Отправляем email клиенту
            self.send_customer_email(cart)
            
            # Отправляем email администратору
            self.send_admin_email(cart)
            
            return Response({
                'message': 'Заказ успешно оформлен',
                'order_id': cart.id
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_customer_email(self, order):
        """Отправка подтверждения клиенту"""
        subject = f'Подтверждение заказа №{order.id}'
        message = f'''
        Уважаемый {order.user.username}!
        
        Ваш заказ №{order.id} успешно оформлен.
        
        Состав заказа:
        {self.format_order_items(order)}
        
        Общая сумма: {order.get_total_sum()} руб.
        
        Адрес доставки: {order.contact.value}
        
        Спасибо за покупку!
        '''
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [order.user.email],
            fail_silently=False,
        )
    
    def send_admin_email(self, order):
        """Отправка накладной администратору"""
        subject = f'Новый заказ №{order.id}'
        message = f'''
        Новый заказ №{order.id}
        
        Клиент: {order.user.username} ({order.user.email})
        Адрес доставки: {order.contact.value}
        
        Состав заказа:
        {self.format_order_items(order)}
        
        Общая сумма: {order.get_total_sum()} руб.
        
        Необходимо собрать заказ.
        '''
        
        # Здесь можно указать email администратора
        admin_email = 'admin@example.com'
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [admin_email],
            fail_silently=False,
        )
    
    def format_order_items(self, order):
        items_text = ""
        for item in order.items.all():
            items_text += f"- {item.product_info.name}: {item.quantity} шт. x {item.product_info.price} руб. = {item.quantity * item.product_info.price} руб.\n"
        return items_text


class OrderListView(generics.ListAPIView):
    """Список заказов пользователя"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).exclude(status='basket').order_by('-dt')


class OrderDetailView(generics.RetrieveAPIView):
    """Детали заказа"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    lookup_url_kwarg = 'order_id'
    
    def get_queryset(self):
        return Order.objects.all()
    
    def get_object(self):
        obj = super().get_object()
        # Дополнительная проверка владельца
        if obj.user != self.request.user:
            self.permission_denied(
                self.request, 
                message="У вас нет прав для просмотра этого заказа"
            )
        return obj


class SupplierOrderListView(generics.ListAPIView):
    """Список заказов для поставщика"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        try:
            shop = Shop.objects.get(user=self.request.user)
            return Order.objects.filter(
                items__shop=shop,
                status__in=['new', 'confirmed', 'assembled']
            ).distinct()
        except Shop.DoesNotExist:
            return Order.objects.none()


class SupplierOrderDetailView(generics.RetrieveUpdateAPIView):
    """Детали заказа для поставщика с возможностью изменения статуса"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_url_kwarg = 'order_id'
    
    def get_queryset(self):
        try:
            shop = Shop.objects.get(user=self.request.user)
            return Order.objects.filter(items__shop=shop).distinct()
        except Shop.DoesNotExist:
            return Order.objects.none()
    
    def patch(self, request, *args, **kwargs):
        """Обновление статуса заказа"""
        order = self.get_object()
        serializer = OrderStatusSerializer(data=request.data)
        
        if serializer.is_valid():
            order.status = serializer.validated_data['status']
            order.save()
            return Response(OrderSerializer(order).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShopUpdateView(generics.RetrieveUpdateAPIView):
    """Обновление информации о магазине (вкл/выкл прием заказов)"""
    serializer_class = ShopSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return get_object_or_404(Shop, user=self.request.user)