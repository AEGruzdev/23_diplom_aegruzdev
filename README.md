# документация Django-приложения "Сервис заказа товаров"

## Содержание
### 1 Общее описание
### 2 Установка и настройка
### 3 Модели данных
### 4 API Endpoints
### 5 Аутентификация
### 6 Импорт товаров
### 7 Примеры использования
### 8 Развертывание на сервере
### 9 Часто задаваемые вопросы


### Общее описание
Приложение представляет собой backend-часть сервиса для автоматизации закупок в розничной сети, аналогичного российским маркетплейсам (Ozon, Wildberries). Система позволяет:

- Клиентам: просматривать каталог товаров, формировать корзину, оформлять заказы
- Поставщикам: управлять прайс-листами, включать/отключать прием заказов, отслеживать заказы
- Администраторам: управлять всеми сущностями через админ-панель

#### Ключевые возможности

- REST API с полной документацией (Swagger/ReDoc)
- Поддержка PostgreSQL
- Импорт товаров из JSON/YAML файлов
- Email-уведомления при оформлении заказов
- Корзина с товарами от разных поствщиков
- Разграничение прав доступа (клиент/поставщик/админ)


### Установка и настройка

#### 1. Клонирование репозитория
git clone <url-репозитория>
cd 023_diplom_d

#### 2. Создание виртуального окружения
###### Windows
python -m venv venv
venv\Scripts\activate

###### Linux/Mac
python3 -m venv venv
source venv/bin/activate

#### 3. Установка зависимостей
pip install -r requirements.txt

#### 4. Настройка PostgreSQL
###### Установка PostgreSQL (Windows)
1 Скачайте установщик с официального сайта
2 Запомните пароль для пользователя postgres
3 Добавьте C:\Program Files\PostgreSQL\<версия>\bin в PATH

###### Создание базы данных
# Войдите в psql
psql -U postgres

# Выполните SQL команды
CREATE DATABASE diplom_db;
CREATE USER diplom_user WITH PASSWORD 'secure_password';
ALTER ROLE diplom_user SET client_encoding TO 'utf8';
ALTER ROLE diplom_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE diplom_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE diplom_db TO diplom_user;
\q

#### 5. Настройка переменных окружения
Заполните файл .env

#### 6. Применение миграций
python manage.py makemigrations api
python manage.py migrate

#### 7. Создание суперпользователя
python manage.py createsuperuser

#### 8. Запуск сервера
python manage.py runserver
После запуска сервер будет доступен по адресу: http://127.0.0.1:8000/


### Модели данных
#### Описание моделей

##### User (встроенная модель Django)
Поле	             Тип	               Описание
username	         CharField	           Имя пользователя
email	             EmailField	           Email
first_name	         CharField	           Имя
last_name	         CharField	           Фамилия
password	         CharField	           Пароль

##### Shop (Магазин/Поставщик)
Поле	             Тип	               Описание
name	             CharField	           Название магазина
url	                 URLField	           Сайт магазина
user	             OneToOneField	       Связь с пользователем-владельцем
state	             BooleanField	       Статус приема заказов

##### Category (Категория товаров)
Поле	             Тип	               Описание
name	             CharField	           Название категории
shops	             ManyToManyField	   Магазины в этой категории

##### Product (Товар)
Поле	             Тип	               Описание
name	             CharField	           Название товара
category	         ForeignKey	           Категория товара

##### ProductInfo (Информация о товаре в магазине)
Поле	             Тип	               Описание
product	             ForeignKey	           Ссылка на товар
shop	             ForeignKey	           Ссылка на магазин
name	             CharField	           Название в конкретном магазине
quantity	         PositiveIntegerField  Количество на складе
price	             DecimalField	       Цена
price_rrc	         DecimalField	       Рекомендуемая цена

##### Parameter (Параметр товара)
Поле	             Тип	               Описание
name	             CharField	           Название параметра

##### ProductParameter (Значение параметра)
Поле	             Тип	               Описание
product_info	     ForeignKey	           Ссылка на информацию о товаре
parameter	         ForeignKey	           Ссылка на параметр
value	             CharField	           Значение параметра

##### Contact (Контакт пользователя)
Поле	             Тип	               Описание
type	             CharField	           Тип (email/phone/address)
user	             ForeignKey	           Ссылка на пользователя
value	             CharField	           Значение контакта

##### Order (Заказ)
Поле	             Тип	               Описание
user	             ForeignKey	           Ссылка на пользователя
dt	                 DateTimeField	       Дата и время заказа
status	             CharField	           Статус заказа
contact	             ForeignKey	           Адрес доставки

### API Endpoints
#### Базовый URL
http://localhost:8000/api/

#### Документация API
Swagger UI: http://localhost:8000/swagger/
ReDoc: http://localhost:8000/redoc/

#### Аутентификация

Метод	                Endpoint	             Описание	                             Доступ
POST	                /auth/register/	         Регистрация нового пользователя	     Public
POST	                /auth/token/login/	     Получение токена	                     Public
POST	                /auth/token/logout/	     Выход из системы	                     Authenticated
GET	                    /auth/users/	         Список пользователей	                 Admin
GET	                    /auth/users/me/	         Профиль текущего пользователя	         Authenticated

#### Профиль и контакты

Метод	                Endpoint	             Описание	                             Доступ
GET/PUT	                /profile/	             Получение/обновление профиля	         Authenticated
GET	                    /contacts/	             Список контактов	                     Authenticated
POST	                /contacts/	             Создание контакта	                     Authenticated
GET	                    /contacts/{id}/	         Детали контакта	                     Authenticated
PUT/PATCH	            /contacts/{id}/	         Обновление контакта	                 Authenticated
DELETE	                /contacts/{id}/	         Удаление контакта	                     Authenticated

#### Товары

Метод	                Endpoint	             Описание	                             Доступ
GET	                    /products/	             Список товаров	                         Public
GET	                    /products/{id}/	         Детали товара	                         Public

Параметры фильтрации для /products/:

?category=1 - фильтр по категории
?shop=1 - фильтр по магазину
?search=iphone - поиск по названию
?ordering=price - сортировка (price, -price, name, -name)

#### Корзина

Метод	                 Endpoint	             Описание	                             Доступ
GET	                     /cart/	                 Получение корзины	                     Authenticated
POST	                 /cart/	                 Добавление товара	                     Authenticated
PUT	                     /cart/                	 Обновление количества	                 Authenticated
DELETE	                 /cart/	                 Удаление товара 	                     Authenticated

###### Формат запроса POST/PUT:
{
    "product_info": 1,
    "quantity": 2
}

###### Формат запроса DELETE:
{
    "item_id": 5
}

#### Заказы

Метод	                  Endpoint	              Описание	                            Доступ
GET	                      /orders/	              Список заказов	                    Authenticated
GET	                      /orders/{id}/	          Детали заказа	                        Authenticated
POST	                  /orders/confirm/	      Подтверждение заказа	                Authenticated

#### Поставщики

Метод	                  Endpoint	              Описание	                            Доступ
GET	                      /supplier/orders/	      Заказы поставщика	                    Supplier
GET	                      /supplier/orders/{id}/  Детали заказа	                        Supplier
PATCH	                  /supplier/orders/{id}/  Обновление статуса	                Supplier
GET/PUT	                  /supplier/shop/	      Управление магазином	                Supplier


### Аутентификация
#### Типы пользователей

##### 1 Анонимный пользователь
- Может просматривать товары
- Не может создавать заказы

##### 2 Клиент (зарегистрированный пользователь)
- Все права анонимного пользователя
- Может управлять контактами
- Может работать с корзиной
- Может оформлять заказы
- Может просматривать свои заказы

##### 3 Поставщик (пользователь, связанный с магазином)
- Все права клиента
- Может управлять своим магазином
- Может просматривать заказы, содержащие его товары
- Может изменять статус заказов

##### 4 Администратор
- Полный доступ ко всем функциям через админ-панель
- Управление пользователями
- Управление всеми заказами

#### Получение токена
curl -X POST http://localhost:8000/api/auth/token/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123"
  }'

##### Ответ:
{
    "auth_token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}

##### Использование токена
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"


### Импорт товаров

#### JSON формат
{
  "shop": {
    "name": "Электронный мир",
    "url": "https://electronic-world.ru"
  },
  "categories": [
    {"name": "Смартфоны"},
    {"name": "Ноутбуки"}
  ],
  "goods": [
    {
      "name": "iPhone 14",
      "category": "Смартфоны",
      "price": 89990,
      "price_rrc": 89990,
      "quantity": 10,
      "parameters": {
        "Процессор": "A16 Bionic",
        "Память": "128GB",
        "Цвет": "Черный"
      }
    }
  ]
}

#### YAML формат
shop:
  name: "Электронный мир"
  url: "https://electronic-world.ru"

categories:
  - name: "Смартфоны"
  - name: "Ноутбуки"

goods:
  - name: "iPhone 14"
    category: "Смартфоны"
    price: 89990
    price_rrc: 89990
    quantity: 10
    parameters:
      Процессор: "A16 Bionic"
      Память: "128GB"
      Цвет: "Черный"

#### Результат импорта
Начинаю импорт из ./data...
Импорт завершен:
  Обработано файлов: 3
  Магазинов: 3
  Категорий: 8
  Товаров: 25
  Информаций о товарах: 25
  Параметров: 42

  
### Примеры использования
#### Полный цикл работы клиента

##### 1 Регистрация
  curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ivan_petrov",
    "password": "SecurePass123",
    "password2": "SecurePass123",
    "email": "ivan@example.com",
    "first_name": "Иван",
    "last_name": "Петров"
  }'

##### 2. Авторизация
  curl -X POST http://localhost:8000/api/auth/token/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ivan_petrov",
    "password": "SecurePass123"
  }'

Сохраните токен
TOKEN="полученный_токен"

##### 3. Добавление адреса доставки
curl -X POST http://localhost:8000/api/contacts/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "address",
    "value": "г. Москва, ул. Ленина, д. 10, кв. 5"
  }'

Сохраните ID контакта
CONTACT_ID=1

##### 4. Просмотр товаров
Все товары
curl -X GET "http://localhost:8000/api/products/"

С фильтрацией
curl -X GET "http://localhost:8000/api/products/?category=1&search=iphone&ordering=-price"

##### 5. Добавление товаров в корзину
Добавить первый товар
curl -X POST http://localhost:8000/api/cart/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_info": 1,
    "quantity": 2
  }'

Добавить второй товар из другого магазина
curl -X POST http://localhost:8000/api/cart/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_info": 3,
    "quantity": 1
  }'

##### 6. Просмотр корзины
curl -X GET http://localhost:8000/api/cart/ \
  -H "Authorization: Token $TOKEN"

##### 7. Оформление заказа
curl -X POST http://localhost:8000/api/orders/confirm/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"contact_id\": $CONTACT_ID}"

##### 8. Просмотр заказов
Список заказов
curl -X GET http://localhost:8000/api/orders/ \
  -H "Authorization: Token $TOKEN"

Детали конкретного заказа
curl -X GET http://localhost:8000/api/orders/1/ \
  -H "Authorization: Token $TOKEN"

#### Пример работы поставщика

##### 1. Привязка пользователя к магазину (через админку)
Войдите в админ-панель и создайте магазин, привязав его к пользователю-поставщику.

##### 2. Просмотр заказов
curl -X GET http://localhost:8000/api/supplier/orders/ \
  -H "Authorization: Token $TOKEN_SUPPLIER"

##### 3. Изменение статуса заказа
curl -X PATCH http://localhost:8000/api/supplier/orders/1/ \
  -H "Authorization: Token $TOKEN_SUPPLIER" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "assembled"
  }'

##### 4. Управление приемом заказов
Отключить прием заказов
curl -X PATCH http://localhost:8000/api/supplier/shop/ \
  -H "Authorization: Token $TOKEN_SUPPLIER" \
  -H "Content-Type: application/json" \
  -d '{
    "state": false
  }'

Включить прием заказов
curl -X PATCH http://localhost:8000/api/supplier/shop/ \
  -H "Authorization: Token $TOKEN_SUPPLIER" \
  -H "Content-Type: application/json" \
  -d '{
    "state": true
  }'

### Развертывание на сервере

#### Настройка для production

##### 1. Изменение настроек в settings.py

DEBUG = False

ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

Настройка CORS для продакшена
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://your-domain.com",
    "https://www.your-domain.com",
]

Настройка базы данных (используйте .env)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

Настройка email для продакшена
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

##### 2. Установка и настройка Gunicorn

pip install gunicorn

Создание файла службы (для Linux)
sudo nano /etc/systemd/system/gunicorn.service

###### ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=your_user
Group=www-data
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/your/project/venv/bin/gunicorn --workers 3 --bind unix:/path/to/your/project/backend.sock backend.wsgi:application

[Install]
WantedBy=multi-user.target

##### 3. Настройка Nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /path/to/your/project;
    }

    location /media/ {
        root /path/to/your/project;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/your/project/backend.sock;
    }
}

##### 4. Настройка SSL с Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com


### Часто задаваемые вопросы

#### 1. Как сбросить пароль пользователя?
терминал
python manage.py shell

python
from django.contrib.auth.models import User
user = User.objects.get(username='username')
user.set_password('new_password')
user.save()

#### 2. Как очистить корзину пользователя?
терминал
python manage.py shell

python
from api.models import Order
Order.objects.filter(user__username='username', status='basket').delete()

#### 3. Как сделать пользователя поставщиком?
Через админ-панель:

Создайте магазин (Shop)
В поле user выберите пользователя
Сохраните

Через код:

from django.contrib.auth.models import User
from api.models import Shop

user = User.objects.get(username='supplier')
shop = Shop.objects.create(
    name='Магазин поставщика',
    url='https://example.com',
    user=user,
    state=True
)

#### 4. Как обновить прайс-лист?
python manage.py import_data /path/to/new/pricelist/

#### 5. Почему не приходят email?
Проверьте:

Настройки SMTP в .env файле
Не используется ли EMAIL_BACKEND = 'console.EmailBackend'
Не блокирует ли почтовый сервис (для Gmail нужно разрешить "ненадежные приложения")

#### 6. Как сделать резервную копию базы данных?
Для PostgreSQL
pg_dump -U diplom_user diplom_db > backup_$(date +%Y%m%d).sql

Восстановление
psql -U diplom_user diplom_db < backup_file.sql

#### 7. Что делать при ошибке "relation does not exist"?
python manage.py migrate

#### 8. Как добавить нового поставщика через API?
Создайте пользователя через регистрацию, затем в админ-панели привяжите его к магазину.

#### 9. Где посмотреть все заказы поставщика?
Используйте endpoint:
curl -X GET http://localhost:8000/api/supplier/orders/ \
  -H "Authorization: Token $TOKEN_SUPPLIER"

#### Полезные команды для диагностики
Проверка миграций
python manage.py showmigrations

Проверка подключения к БД
python manage.py dbshell

Просмотр логов
tail -f debug.log

Проверка работоспособности
python manage.py check

#### Заключение
Данное приложение предоставляет полный функционал для создания сервиса заказа товаров. Оно готово к использованию как в учебных целях, так и в production-среде с соответствующей настройкой безопасности и масштабирования.