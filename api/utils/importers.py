import json
import yaml
import os
from django.db import transaction
from api.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter


class DataImporter:
    """Класс для импорта данных из файлов"""
    
    @staticmethod
    def import_from_json(file_path):
        """Импорт из JSON файла"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return DataImporter._process_data(data)
    
    @staticmethod
    def import_from_yaml(file_path):
        """Импорт из YAML файла"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        return DataImporter._process_data(data)
    
    @staticmethod
    @transaction.atomic
    def _process_data(data):
        """Обработка данных и сохранение в БД"""
        results = {
            'shops': 0,
            'categories': 0,
            'products': 0,
            'product_infos': 0,
            'parameters': 0
        }
        
        # Создание или обновление магазина
        shop_data = data.get('shop', {})
        shop, created = Shop.objects.update_or_create(
            name=shop_data.get('name'),
            defaults={
                'url': shop_data.get('url', ''),
                'state': True
            }
        )
        results['shops'] += 1
        
        # Импорт категорий
        for cat_data in data.get('categories', []):
            category, _ = Category.objects.get_or_create(
                name=cat_data['name']
            )
            category.shops.add(shop)
            results['categories'] += 1
        
        # Импорт товаров
        for good_data in data.get('goods', []):
            # Получение или создание категории
            category = Category.objects.get(name=good_data['category'])
            
            # Создание или обновление товара
            product, _ = Product.objects.update_or_create(
                name=good_data['name'],
                defaults={'category': category}
            )
            results['products'] += 1
            
            # Создание информации о товаре
            product_info, _ = ProductInfo.objects.update_or_create(
                product=product,
                shop=shop,
                defaults={
                    'name': good_data['name'],
                    'quantity': good_data.get('quantity', 0),
                    'price': good_data['price'],
                    'price_rrc': good_data.get('price_rrc', good_data['price'])
                }
            )
            results['product_infos'] += 1
            
            # Импорт параметров
            for param_name, param_value in good_data.get('parameters', {}).items():
                parameter, _ = Parameter.objects.get_or_create(name=param_name)
                results['parameters'] += 1
                
                ProductParameter.objects.update_or_create(
                    product_info=product_info,
                    parameter=parameter,
                    defaults={'value': str(param_value)}
                )
        
        return results
    
    @staticmethod
    def import_all_from_directory(directory_path):
        """Импорт всех файлов из директории"""
        total_results = {
            'shops': 0,
            'categories': 0,
            'products': 0,
            'product_infos': 0,
            'parameters': 0,
            'files_processed': 0,
            'errors': []
        }
        
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            
            if filename.endswith('.json'):
                try:
                    results = DataImporter.import_from_json(file_path)
                    for key in total_results:
                        if key in results:
                            total_results[key] += results[key]
                    total_results['files_processed'] += 1
                except Exception as e:
                    total_results['errors'].append(f"{filename}: {str(e)}")
                    
            elif filename.endswith(('.yaml', '.yml')):
                try:
                    results = DataImporter.import_from_yaml(file_path)
                    for key in total_results:
                        if key in results:
                            total_results[key] += results[key]
                    total_results['files_processed'] += 1
                except Exception as e:
                    total_results['errors'].append(f"{filename}: {str(e)}")
        
        return total_results