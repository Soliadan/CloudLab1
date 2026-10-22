# CloudLab1 — Flask REST API в AWS

**Репозиторій:** https://github.com/Soliadan/CloudLab1

**Публічна адреса:** http://cloudlab1-lab-1602657390.eu-north-1.elb.amazonaws.com

**Healthcheck:** http://cloudlab1-lab-1602657390.eu-north-1.elb.amazonaws.com/health

Проєкт демонструє повний цикл розробки та розгортання Flask REST API з PostgreSQL: локальний запуск через Docker Compose, інфраструктура в AWS через Terraform, приватна база даних, Application Load Balancer і CI/CD через GitHub Actions з OIDC.

## Що реалізовано

| № | Завдання | Реалізація |
|---|---|---|
| 1 | Docker + PostgreSQL | Flask API і PostgreSQL запускаються через `docker compose`; дані зберігаються у volume `postgres_data`. |
| 2 | Terraform + ECR + RDS + ECS | Інфраструктура описана в `infra/`; використовується ECS Fargate, ECR і приватний RDS PostgreSQL. |
| 3 | Private subnets і Security Groups | RDS не має публічного доступу; DB Security Group приймає трафік лише від app Security Group. |
| 4 | ALB і `/health` | Internet-facing ALB є єдиною публічною точкою; target group перевіряє `/health`. |
| 5 | CI/CD через GitHub OIDC | GitHub Actions отримує тимчасові AWS-credentials через OIDC, збирає image з тегом commit SHA і оновлює ECS. |

## Архітектура AWS

```text
Internet
   │
   ▼
Application Load Balancer :80
   │  public subnets
   ▼
ECS Fargate :8088
   │  private subnets
   ▼
RDS PostgreSQL :5432
   │  private subnets
   ▼
Secrets Manager
```

- ALB приймає HTTP-трафік і перевіряє target через `/health`.
- ECS task не має public IP.
- RDS доступний лише з app Security Group.
- NAT Gateway потрібен ECS для доступу до ECR, CloudWatch Logs і Secrets Manager.
- Пароль RDS генерується AWS і зберігається в Secrets Manager; ECS читає його через `secrets`, а не через відкритий текст.

## Структура проєкту

```text
.
├── compose.yaml                  # локальний API + PostgreSQL + volume
├── .env.example                  # шаблон локальних змінних
├── perfume_backend/
│   ├── Dockerfile                # образ API
│   ├── docker-entrypoint.sh      # ініціалізація схеми перед стартом
│   ├── main_pg.py                # Flask REST API
│   ├── database_pg.py            # підключення до PostgreSQL
│   ├── schema.sql                # таблиця orders
│   ├── index.html                # веб-інтерфейс
│   ├── static/
│   │   ├── css/styles.css
│   │   └── js/index.js
│   └── requirements.txt
├── infra/                        # основний Terraform-стек AWS
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── terraform/
│   ├── state-bootstrap/          # S3 bucket для Terraform state
│   └── budget/                   # AWS Budget
├── .github/workflows/
│   ├── ci.yml                    # тести, lint, Docker build, Terraform validate
│   └── deploy.yml                # OIDC deployment в ECS
├── tests/test_api.py
├── requirements.txt
└── README.md
```

## Локальний запуск

```sh
cp .env.example .env
# встановити DB_PASSWORD у .env

docker compose config --quiet
docker compose up -d --build --wait
docker compose ps
curl -i http://127.0.0.1:8088/health
```

Сайт локально: `http://127.0.0.1:8088`

Не виконувати `docker compose down -v`: ця команда видаляє volume `postgres_data` разом з даними.

## API

| Метод | Шлях | Призначення |
|---|---|---|
| GET | `/` | Веб-інтерфейс |
| GET | `/health` | Перевірка API і доступності таблиці `orders` |
| GET | `/orders` | Список замовлень |
| GET | `/orders/{id}` | Одне замовлення |
| POST | `/orders` | Створити замовлення |
| PUT / PATCH | `/orders/{id}` | Оновити замовлення |
| DELETE | `/orders/{id}` | Видалити замовлення |

Приклад створення:

```sh
curl -i -X POST http://127.0.0.1:8088/orders \
  -H 'Content-Type: application/json' \
  -d '{"parfume_name":"Rose","Volume":"50ml","brand":"Lab","order_date":"2026-10-20","price":100}'
```

Коди відповідей: `201` — створено, `204` — видалено, `400` — неправильні дані, `404` — не знайдено, `409` — дубль ID, `503` — база недоступна.

## Секрети та конфігурація

- Локально пароль передається через `.env`; `.env` не комітиться.
- У хмарі пароль RDS зберігається в AWS Secrets Manager.
- ECS отримує пароль через `secrets`, а не через `environment`.
- `infra/backend.hcl`, `terraform.tfvars` і `private-artifacts/` ігноруються Git.
- CI/CD не використовує довговічні AWS access keys: доступ видається через GitHub OIDC і IAM role.

## Terraform

- `infra/` — основний стек: VPC, subnets, Security Groups, ALB, ECR, ECS Fargate, RDS, IAM і OIDC.
- `terraform/state-bootstrap/` — окремий root для S3 bucket, у якому зберігається Terraform state.
- `terraform/budget/` — окремий root для наявного AWS Budget.
- Приватні backend/tfvars не зберігаються в репозиторії.
- `terraform apply` і `terraform destroy` виконуються лише після перевірки плану та окремого дозволу.

## CI/CD

- `ci.yml` перевіряє compose-конфігурацію, запускає тести на окремій PostgreSQL, виконує lint, збирає Docker image і перевіряє Terraform.
- `deploy.yml` запускається після успішного `Checks` для `main`.
- Деплой отримує тимчасові credentials через OIDC, збирає image з повним commit SHA, оновлює ECS і перевіряє `/health`.
- У разі невдачі повертається попередня task definition.

## Тести

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/ruff check perfume_backend tests --select E9,F63,F7,F82
terraform fmt -recursive -check
terraform -chdir=infra validate
```

Локально: **11 passed, 1 skipped**. Пропущений тест потребує окремої PostgreSQL через `TEST_DATABASE_URL`; робочу базу для нього не використовувати.

## Поточний стан

- ECS Fargate service: `1/1` running.
- ALB target: healthy.
- RDS: private, `PubliclyAccessible=false`.
- Публічний `/health`: HTTP 200.
- AWS-доступ CI/CD: OIDC, без статичних ключів.
