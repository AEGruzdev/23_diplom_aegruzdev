from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'type', 'value']
        read_only_fields = ['user']


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'url', 'state']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'category']


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ['id', 'name']


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = ParameterSerializer(read_only=True)
    
    class Meta:
        model = ProductParameter
        fields = ['id', 'parameter', 'value']


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    parameters = ProductParameterSerializer(source='product_parameters', many=True, read_only=True)
    
    class Meta:
        model = ProductInfo
        fields = ['id', 'product', 'shop', 'name', 'quantity', 'price', 'price_rrc', 'parameters']


class OrderItemSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_info', 'shop', 'quantity', 'total_price']
        read_only_fields = ['shop']
    
    def get_total_price(self, obj):
        return obj.quantity * obj.product_info.price


class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_info', 'quantity']
    
    def validate(self, attrs):
        product_info = attrs['product_info']
        quantity = attrs['quantity']
        
        if quantity > product_info.quantity:
            raise serializers.ValidationError(
                f"Доступно только {product_info.quantity} шт."
            )
        
        if not product_info.shop.state:
            raise serializers.ValidationError(
                f"Магазин {product_info.shop.name} временно не принимает заказы"
            )
        
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    contact = ContactSerializer(read_only=True)
    total_sum = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'dt', 'status', 'contact', 'items', 'total_sum']
        read_only_fields = ['user', 'dt']
    
    def get_total_sum(self, obj):
        return sum(item.quantity * item.product_info.price for item in obj.items.all())


class OrderConfirmSerializer(serializers.Serializer):
    contact_id = serializers.IntegerField()
    
    def validate_contact_id(self, value):
        try:
            contact = Contact.objects.get(id=value)
            if contact.type != 'address':
                raise serializers.ValidationError("Контакт должен быть адресом доставки")
            return value
        except Contact.DoesNotExist:
            raise serializers.ValidationError("Контакт не найден")


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']