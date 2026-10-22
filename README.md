# Лабораторна робота №1

# Perfume Shop API: розгортання в AWS (Terraform)

REST API для роботи із замовленнями парфумів на Flask і PostgreSQL. Застосунок запускається локально через Docker Compose та розгортається в AWS за допомогою Terraform. Автоматичне оновлення налаштоване через GitHub Actions.

**Репозиторій:** https://github.com/Soliadan/CloudLab1

**Публічна адреса:** http://cloudlab1-lab-1602657390.eu-north-1.elb.amazonaws.com

**Health check:** http://cloudlab1-lab-1602657390.eu-north-1.elb.amazonaws.com/health

## Ендпоінти

| Метод | Шлях | Призначення |
|---|---|---|
| GET | `/` | Головна сторінка |
| GET | `/health` | Перевірка API та бази даних |
| GET | `/orders` | Перегляд замовлень |
| GET | `/orders/<id>` | Замовлення за ID |
| POST | `/orders` | Створення замовлення |
| PUT, PATCH | `/orders/<id>` | Редагування замовлення |
| DELETE | `/orders/<id>` | Видалення замовлення |

Усі замовлення зберігаються в PostgreSQL.

## Структура репозиторію

| Файл | Призначення |
|---|---|
| `perfume_backend/main_pg.py` | Flask API та ендпоінти |
| `perfume_backend/database_pg.py` | Підключення до PostgreSQL |
| `perfume_backend/schema.sql` | Створення таблиці orders |
| `perfume_backend/requirements.txt` | Бібліотеки Python |
| `perfume_backend/Dockerfile` | Збірка Docker-образу |
| `compose.yaml` | Локальний запуск API та PostgreSQL |
| `infra/main.tf` | Основна AWS-інфраструктура |
| `infra/variables.tf` | Змінні Terraform |
| `infra/outputs.tf` | Адреси та параметри створених ресурсів |
| `infra/versions.tf` | Провайдер і налаштування Terraform |
| `terraform/state-bootstrap/` | S3 bucket для Terraform state |
| `terraform/budget/` | AWS Budget |
| `.github/workflows/ci.yml` | Перевірки коду та Docker |
| `.github/workflows/deploy.yml` | Автоматичний deployment |

## Локальний запуск

Для локального запуску використовується Docker Compose. Він запускає Flask API та PostgreSQL в окремих контейнерах.

Спочатку потрібно створити `.env` із шаблону `.env.example` та вказати пароль бази даних.

```bash
cp .env.example .env
docker compose up -d --build --wait
```

Перевірка:

```bash
curl http://localhost:8088/health
curl http://localhost:8088/orders
```

Зупинити контейнери:

```bash
docker compose down
```

Дані PostgreSQL зберігаються у volume `postgres_data` і залишаються після звичайного `docker compose down`.

У Dockerfile використано зафіксовану версію базового образу. Залежності встановлюються окремим шаром, а застосунок запускається не від root.

## Розгортання в AWS

Інфраструктура описана Terraform.

| Сервіс | Призначення |
|---|---|
| Amazon ECR | Реєстр Docker-образів |
| Amazon ECS Fargate | Запуск Flask-контейнера |
| Amazon RDS | PostgreSQL у хмарі |
| Amazon VPC | Мережа та підмережі |
| Security Groups | Контроль мережевого доступу |
| Application Load Balancer | Публічний доступ до API |
| AWS Secrets Manager | Зберігання пароля бази |
| IAM та OIDC | Доступ GitHub Actions до AWS |
| Amazon S3 | Зберігання Terraform state |

Основна конфігурація розташована в `infra/`.

```bash
cd infra
terraform init -backend-config=backend.hcl
terraform validate
terraform plan
terraform apply
terraform output
```

Перед першим розгортанням потрібно створити S3 backend через `terraform/state-bootstrap/`. Для початкового запуску також потрібно завантажити Docker-образ у ECR та створити таблицю в RDS.

## Мережа та безпека

Вхідний трафік проходить через Application Load Balancer, який пересилає запити до ECS Fargate.

Схема роботи:

```text
Internet
   |
   v
Application Load Balancer :80
   |
   v
ECS Fargate :8088
   |
   v
RDS PostgreSQL :5432
```

ALB розміщений у публічних підмережах. ECS та RDS працюють у приватних.

База даних не має публічної IP-адреси. Її Security Group дозволяє підключення на порт 5432 лише від Security Group застосунку.

ECS приймає запити на порт 8088 тільки від ALB. Для перевірки доступності використовується `/health` з очікуваним кодом HTTP 200.

Пароль RDS зберігається в AWS Secrets Manager і передається контейнеру під час запуску. Локальні паролі та приватні Terraform-конфігурації не додаються до GitHub.

## CI/CD

Автоматичне розгортання виконується через GitHub Actions.

Після push у гілку `main` запускається перевірка коду, а після успішного завершення — deployment.

```text
Push to main
     |
     v
GitHub Actions
     |
     v
Docker build
     |
     v
Amazon ECR (commit SHA)
     |
     v
Amazon ECS Fargate
     |
     v
Application Load Balancer
```

Для доступу до AWS використовується OIDC та IAM Role без постійних access keys.

Новий Docker-образ отримує тег із SHA коміту та завантажується в ECR. Після цього GitHub Actions оновлює task definition в ECS і перевіряє розгортання.

## Перевірка API

Отримати всі замовлення:

```bash
curl http://localhost:8088/orders
```

Створити замовлення:

```bash
curl -X POST http://localhost:8088/orders \
-H "Content-Type: application/json" \
-d '{
  "parfume_name": "Rose",
  "Volume": "50ml",
  "brand": "Lab",
  "order_date": "2026-10-20",
  "price": 100
}'
```

Після створення запис можна переглянути через `GET /orders`.

У AWS використовуються ті самі API-ендпоінти через публічну адресу ALB.

## Видалення інфраструктури

Для видалення основної інфраструктури:

```bash
cd infra
terraform plan -destroy
terraform destroy
```

S3 backend і AWS Budget керуються окремими Terraform-конфігураціями. Їх необхідно перевірити та видалити окремо, якщо потрібно повністю очистити AWS-акаунт від ресурсів лабораторної.