FROM python:3.14.8-slim-trixie@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY Projects/employee_management_system/requirements-deploy.txt /tmp/requirements.txt
COPY Projects/employee_management_system/requirements-security.txt /tmp/requirements-security.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN groupadd --gid 10001 abap && useradd --uid 10001 --gid abap --no-create-home abap
COPY Projects/employee_management_system/ /app/
RUN find /app -type d -exec chmod 0555 {} + \
    && find /app -type f -exec chmod 0444 {} + \
    && mkdir -p /app/logs /app/data/documents /app/exports \
    && chown -R abap:abap /app/logs /app/data /app/exports \
    && chmod 0750 /app/logs /app/data /app/data/documents /app/exports
USER abap
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "deployment:create_application", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
