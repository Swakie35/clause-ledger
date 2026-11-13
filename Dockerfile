FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY clauseledger ./clauseledger
RUN pip install --no-cache-dir . && useradd -m appuser && mkdir /data && chown appuser /data
USER appuser
WORKDIR /data
EXPOSE 8000
CMD ["uvicorn", "clauseledger.api:app", "--host", "0.0.0.0", "--port", "8000"]
