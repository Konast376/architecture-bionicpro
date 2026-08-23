# Описание для задания 2

### Airflow DAG

Файл: `airflow/dags/reports_etl.py`.
DAG запускается каждый час по расписанию.

Итоговая витрина: `reports.reports_mart`.

### Backend API

Backend написан на Python/FastAPI.

```http
GET /reports
Authorization: Bearer <Keycloak access token>
```

API читает уже подготовленную ClickHouse-витрину, поэтому не выполняет тяжёлые вычисления в момент запроса.

### Доступ только к собственному отчёту

Пользователь определяется по `sub` из JWT Keycloak. Основной запрос не принимает идентификатор другого пользователя:

```http
GET /reports
```

### UI

`frontend/src/components/ReportPage.tsx` содержит кнопку **Get Report**. Она вызывает `/reports`, отображает ответ таблицей и позволяет скачать JSON.

# Запуск

## Требования

Docker Desktop + Docker Compose

## Команда

```bash
docker compose up --build
```

Сервисы:

| Сервис                | URL                        |
|-----------------------|----------------------------|
| Frontend              | http://localhost:3000      |
| Reports API / Swagger | http://localhost:8000/docs |
| Keycloak              | http://localhost:8080      |
| Airflow               | http://localhost:8081      |
| ClickHouse HTTP       | http://localhost:8123      |

Airflow: `admin / admin`.

Keycloak Admin Console: `admin / admin`.

## Проверить UI

Откройте `http://localhost:3000`.

Тестовый пользователь:

```text
prothetic1 / prothetic123
```

После входа нажмите **Get Report**.