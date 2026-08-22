from __future__ import annotations

import os
from datetime import date, datetime

import clickhouse_connect
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .auth import AuthenticatedUser, current_user

app = FastAPI(title='BionicPRO Reports API', version='1.1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv('FRONTEND_ORIGIN', 'http://localhost:3000'),
        'http://127.0.0.1:3000',
    ],
    allow_credentials=True,
    allow_methods=['GET', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type'],
)


def clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.getenv('CLICKHOUSE_HOST', 'clickhouse'),
        port=int(os.getenv('CLICKHOUSE_PORT', '8123')),
        username=os.getenv('CLICKHOUSE_USER', 'default'),
        password=os.getenv('CLICKHOUSE_PASSWORD', ''),
        database=os.getenv('CLICKHOUSE_DATABASE', 'reports'),
    )


class ReportRow(BaseModel):
    report_date: date
    prosthesis_id: str
    prosthesis_model: str
    events_count: int
    successful_actions: int
    error_count: int
    avg_signal_strength: float
    avg_battery_pct: float
    last_event_at: datetime
    generated_at: datetime


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.get('/reports', response_model=list[ReportRow])
def reports(
    user_id: str | None = Query(
        default=None,
        description='Optional diagnostic value. If supplied, it must identify the authenticated user.',
    ),
    user: AuthenticatedUser = Depends(current_user),
) -> list[dict]:
    # Both values come from a cryptographically verified Keycloak token.
    # This preserves the rule that a user can request only their own report.
    allowed_user_ids = {user.subject}
    if user.username:
        allowed_user_ids.add(user.username)

    if user_id is not None and user_id not in allowed_user_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can request reports only for yourself',
        )

    result = clickhouse_client().query(
        '''
        SELECT
            report_date,
            prosthesis_id,
            prosthesis_model,
            events_count,
            successful_actions,
            error_count,
            avg_signal_strength,
            avg_battery_pct,
            last_event_at,
            generated_at
        FROM reports.reports_mart FINAL
        WHERE auth_user_id = {subject:String}
           OR ({username:String} != '' AND username = {username:String})
        ORDER BY report_date DESC, prosthesis_id
        ''',
        parameters={
            'subject': user.subject,
            'username': user.username or '',
        },
    )
    return [dict(zip(result.column_names, row)) for row in result.result_rows]
