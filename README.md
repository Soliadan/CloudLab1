# CloudLab1 — Flask REST API в AWS

Лабораторна за п’ятьма обов’язковими завданнями: Flask + Docker + PostgreSQL; Terraform + ECR/RDS/ECS Fargate; private subnets і Security Groups; ALB HTTP:80 з `/health`; GitHub Actions з OIDC та image tag = commit SHA. Повної методички у workspace немає, тому відповідність перевірено за вимогами власника.

## Структура та принцип роботи

- `perfume_backend/`: `main_pg.py` — REST API; `database_pg.py` — підключення й явна ініціалізація PostgreSQL; `schema.sql` — таблиця orders; Dockerfile і runtime залежності. `migrate_data.py` потрібен для перенесення збережених локальних SQLite-даних, автоматично не запускається.
- `compose.yaml`, `.env.example`: локальний API та PostgreSQL із persistent volume. Dockerfile має pinned base image за SHA256, non-root UID 10001 і Gunicorn.
- `infra/`: `main.tf` містить ресурси лабораторної, `variables.tf` — параметри, `outputs.tf` — адреси та IDs, `versions.tf` — provider і S3 backend. Lockfile фіксує provider.
- `terraform/state-bootstrap/`: окремий root уже створеного S3 bucket. `terraform/budget/`: збережена конфігурація наявного бюджету з prevent_destroy та gate перед відновленням керування. Ці roots не потрібні для запуску API і не застосовуються разом з infra.
- `.github/workflows/ci.yml`: API/CRUD тести на окремій PostgreSQL, lint, Docker build, Terraform validate. `deploy.yml`: після успішного Checks для push main отримує OIDC credentials, завантажує image з повним SHA перевіреного commit і оновлює ECS з перевіркою та rollback. Ручний запуск повторює тести.
- `tests/test_api.py`, кореневий `requirements.txt`: перевірки та dev залежності; runtime залежності підключаються з `perfume_backend/requirements.txt` без дублювання.

Схема AWS: internet → ALB:80 у двох public subnets → ECS:8088 у private subnets → RDS:5432. DB Security Group приймає з’єднання лише від app Security Group. ECS не має public IP; один NAT потрібен для вихідного доступу до ECR, Logs і Secrets Manager. Пароль генерує RDS, ECS execution role читає його з managed secret. CloudWatch Logs залишений для діагностики контейнера.

## Локальний запуск і API

Якщо `.env` відсутній, скопіювати `.env.example` і встановити DB_PASSWORD. Існуючий `.env` і пароль наявного PostgreSQL volume не перезаписувати.

```sh
docker compose config --quiet
docker compose up -d --build --wait
curl -i http://127.0.0.1:8088/health
curl -i http://127.0.0.1:8088/orders
```

API: GET `/`, `/health`, `/orders`, `/orders/{id}`; POST `/orders`; PUT/PATCH/DELETE `/orders/{id}`. POST повертає 201, DELETE — 204, відсутній ID — 404, дубль ID — 409, неправильні дані — 400, недоступна БД — 503. `/health` перевіряє доступ до таблиці orders. Приклад POST:

```json
{"parfume_name":"Rose","Volume":"50ml","brand":"Lab","order_date":"2026-10-20","price":100}
```

Новий volume отримує schema.sql автоматично. Для явної ініціалізації порожньої бази використовується `python database_pg.py` всередині API container/task: CREATE TABLE IF NOT EXISTS зберігає існуючі orders. `migrate_data.py` читає наявний `perfume.db` без змін і переносить записи без перезапису наявних IDs; запускати лише за потреби й з дозволом на зміну БД. Не виконувати `docker compose down -v`: це видаляє дані.

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/ruff check perfume_backend tests --select E9,F63,F7,F82
terraform fmt -recursive -check
terraform -chdir=infra validate
```

Integration test потребує TEST_DATABASE_URL **окремої тестової PostgreSQL**. CI створює її автоматично. Без URL CRUD-тест пропускається; робочу базу для нього не використовувати.

## AWS, State і завершення лабораторної

Profile `cloudlab`, account `107585009937`, region `eu-north-1`. Використовується існуючий S3 bucket `cloudlab1-state-107585009937-eu-north-1-f2fbb9cf6735`, ключ infra — `cloudlab1/lab/terraform.tfstate`. Приватний `infra/backend.hcl` уже підключений: не змінювати key і не створювати bucket повторно. Bootstrap State, його backup, усі приватні backend/tfvars і старі plans збережені; State та секрети не комітити. `.venv`, `.terraform`, кеші та локальні БД ігноруються Git.

Read-only AWS перевірка дозволила ресурси №2–4 з контекстом регіону; EC2 DryRun підтвердив VPC/subnet/route table/SG. OIDC Provider має SCP explicitDeny. Його реалізація й GitHub role збережені під `enable_github_deployment=false`: це блокує завдання №5, але виключає OIDC з плану №2–4. Не змінювати Advanced Features, Spend Limit, бюджет або SCP. Не замінювати OIDC постійними AWS keys.

Після очищення Terraform і Docker image змінилися: **попередній `private-artifacts/lab-2-4.tfplan` застарів і не повинен застосовуватися**. Перед погодженим розгортанням заново зібрати linux/amd64 image очищеного API, обрати його тег у приватному terraform.tfvars та сформувати новий Plan:

```sh
AWS_PROFILE=cloudlab AWS_REGION=eu-north-1 terraform -chdir=infra plan -input=false
```

Порядок після окремого дозволу на AWS витрати: створити infra з desired_count=0 → завантажити справжній image до ECR з тим самим image_tag → запустити одноразовий ECS task `python database_pg.py` у тих самих private subnets/SG → погоджено встановити desired_count=1 і перевірити ALB `/health` та CRUD. Зміни task definition після першого запуску потрібно явно розгортати в ECS, бо service ігнорує task_definition drift, яким керує CI.

Для №5 потрібне вирішення SCP адміністратором, enable_github_deployment=true та GitHub Variables AWS_REGION, AWS_ROLE_ARN, ECR_REPOSITORY, ECS_CLUSTER, ECS_SERVICE. AWS_DEPLOY_ENABLED=true вмикається лише після дозволу й робочого ECS service. Потрібно продемонструвати успішний автоматичний deployment після push main.

Орієнтир малого stack — приблизно $0.12–0.15/год без credits/tax; NAT, ALB, RDS та IPv4 оплачуються навіть при desired_count=0. Apply/Destroy/Import/Push потребують окремого дозволу. Destroy infra видаляє RDS без фінального snapshot і ECR разом з images; S3 backend і бюджет зберігаються в окремих roots. Історичні task definition revisions CI не повністю керуються Terraform. Budget root не запускати для створення повторного cloud-lab-budget: спочатку відновити authoritative State або окремо погодити import точних поточних налаштувань; очікується no-op plan.

Для завершення потрібні новий переглянутий Plan, погоджене AWS розгортання, доступний HTTP API через ALB і підтверджений Actions/OIDC deployment. Фактичну оцінку визначає викладач за повною методичкою.
