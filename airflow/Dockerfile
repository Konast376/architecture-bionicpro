FROM apache/airflow:2.9.3-python3.11

USER airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-postgres==5.11.2 \
    clickhouse-connect==0.7.19
