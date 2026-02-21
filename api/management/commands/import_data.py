from django.core.management.base import BaseCommand
from api.utils.importers import DataImporter
import os


class Command(BaseCommand):
    help = 'Импорт данных из файлов в директории'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='Путь к директории с файлами')

    def handle(self, *args, **options):
        directory = options['directory']
        
        if not os.path.exists(directory):
            self.stdout.write(self.style.ERROR(f'Директория {directory} не существует'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Начинаю импорт из {directory}...'))
        
        results = DataImporter.import_all_from_directory(directory)
        
        self.stdout.write(self.style.SUCCESS(
            f'\nИмпорт завершен:\n'
            f'  Обработано файлов: {results["files_processed"]}\n'
            f'  Магазинов: {results["shops"]}\n'
            f'  Категорий: {results["categories"]}\n'
            f'  Товаров: {results["products"]}\n'
            f'  Информаций о товарах: {results["product_infos"]}\n'
            f'  Параметров: {results["parameters"]}'
        ))
        
        if results['errors']:
            self.stdout.write(self.style.ERROR('\nОшибки:'))
            for error in results['errors']:
                self.stdout.write(self.style.ERROR(f'  {error}'))