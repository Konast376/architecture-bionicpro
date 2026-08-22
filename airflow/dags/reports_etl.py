from __future__ import annotations

from datetime import datetime
import os

import clickhouse_connect
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook


def ch_client():
    return clickhouse_connect.get_client(
        host=os.getenv('CLICKHOUSE_HOST', 'clickhouse'),
        port=int(os.getenv('CLICKHOUSE_PORT', '8123')),
        username=os.getenv('CLICKHOUSE_USER', 'default'),
        password=os.getenv('CLICKHOUSE_PASSWORD', ''),
        database=os.getenv('CLICKHOUSE_DATABASE', 'reports'),
    )


@dag(
    dag_id='bionicpro_reports_etl',
    description='CRM + prosthesis telemetry -> ClickHouse reporting mart',
    schedule='0 * * * *',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['bionicpro', 'reports', 'etl'],
)
def reports_etl():

    @task
    def ensure_clickhouse_schema() -> None:
        ch = ch_client()
        ch.command('CREATE DATABASE IF NOT EXISTS reports')
        ch.command('''
            CREATE TABLE IF NOT EXISTS reports.crm_clients
            (
                client_id UInt64,
                auth_user_id String,
                username String,
                full_name String,
                email String,
                prosthesis_id String,
                prosthesis_model String,
                country LowCardinality(String),
                updated_at DateTime,
                ingested_at DateTime
            )
            ENGINE = ReplacingMergeTree(ingested_at)
            ORDER BY (client_id, auth_user_id)
        ''')
        ch.command('''
            CREATE TABLE IF NOT EXISTS reports.telemetry_raw
            (
                event_id UInt64,
                client_id UInt64,
                prosthesis_id String,
                event_time DateTime,
                movement LowCardinality(String),
                success UInt8,
                signal_strength Float64,
                battery_pct Float64,
                error_code Nullable(String),
                ingested_at DateTime
            )
            ENGINE = ReplacingMergeTree(ingested_at)
            PARTITION BY toYYYYMM(event_time)
            ORDER BY (client_id, prosthesis_id, event_time, event_id)
        ''')
        ch.command('''
            CREATE TABLE IF NOT EXISTS reports.reports_mart
            (
                auth_user_id String,
                client_id UInt64,
                username String,
                report_date Date,
                prosthesis_id String,
                prosthesis_model String,
                full_name String,
                email String,
                events_count UInt64,
                successful_actions UInt64,
                error_count UInt64,
                avg_signal_strength Float64,
                avg_battery_pct Float64,
                last_event_at DateTime,
                generated_at DateTime
            )
            ENGINE = ReplacingMergeTree(generated_at)
            PARTITION BY toYYYYMM(report_date)
            ORDER BY (auth_user_id, report_date, prosthesis_id)
        ''')

        # Migration for a ClickHouse volume created by the previous project version.
        # CREATE TABLE IF NOT EXISTS does not change an already existing table.
        ch.command('''
            ALTER TABLE reports.reports_mart
            ADD COLUMN IF NOT EXISTS username String AFTER client_id
        ''')

    @task
    def sync_crm_clients() -> int:
        pg = PostgresHook(postgres_conn_id='crm_db')
        rows = pg.get_records('''
            SELECT client_id, auth_user_id, username, full_name, email,
                   prosthesis_id, prosthesis_model, country, updated_at
            FROM clients
        ''')
        if not rows:
            return 0

        now = datetime.utcnow()
        payload = [list(r) + [now] for r in rows]
        ch_client().insert(
            'reports.crm_clients',
            payload,
            column_names=[
                'client_id', 'auth_user_id', 'username', 'full_name', 'email',
                'prosthesis_id', 'prosthesis_model', 'country', 'updated_at', 'ingested_at',
            ],
        )
        return len(payload)

    @task
    def sync_telemetry() -> int:
        pg = PostgresHook(postgres_conn_id='telemetry_db')
        rows = pg.get_records('''
            SELECT event_id, client_id, prosthesis_id, event_time, movement,
                   success, signal_strength, battery_pct, error_code
            FROM telemetry
        ''')
        if not rows:
            return 0

        now = datetime.utcnow()
        payload = [
            [r[0], r[1], r[2], r[3], r[4], 1 if r[5] else 0, r[6], r[7], r[8], now]
            for r in rows
        ]
        ch_client().insert(
            'reports.telemetry_raw',
            payload,
            column_names=[
                'event_id', 'client_id', 'prosthesis_id', 'event_time', 'movement',
                'success', 'signal_strength', 'battery_pct', 'error_code', 'ingested_at',
            ],
        )
        return len(payload)

    @task
    def build_reports_mart() -> None:
        ch_client().command('''
            INSERT INTO reports.reports_mart
            (
                auth_user_id,
                client_id,
                username,
                report_date,
                prosthesis_id,
                prosthesis_model,
                full_name,
                email,
                events_count,
                successful_actions,
                error_count,
                avg_signal_strength,
                avg_battery_pct,
                last_event_at,
                generated_at
            )
            SELECT
                c.auth_user_id,
                c.client_id,
                c.username,
                toDate(t.event_time) AS report_date,
                t.prosthesis_id,
                c.prosthesis_model,
                c.full_name,
                c.email,
                count() AS events_count,
                countIf(t.success = 1) AS successful_actions,
                countIf(t.error_code IS NOT NULL) AS error_count,
                round(avg(t.signal_strength), 4) AS avg_signal_strength,
                round(avg(t.battery_pct), 2) AS avg_battery_pct,
                max(t.event_time) AS last_event_at,
                now() AS generated_at
            FROM reports.telemetry_raw AS t FINAL
            INNER JOIN reports.crm_clients AS c FINAL
                ON c.client_id = t.client_id
               AND c.prosthesis_id = t.prosthesis_id
            GROUP BY
                c.auth_user_id,
                c.client_id,
                c.username,
                report_date,
                t.prosthesis_id,
                c.prosthesis_model,
                c.full_name,
                c.email
        ''')

    schema = ensure_clickhouse_schema()
    crm = sync_crm_clients()
    telemetry = sync_telemetry()

    schema >> [crm, telemetry]
    [crm, telemetry] >> build_reports_mart()


reports_etl()
