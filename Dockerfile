FROM python:3.14.6-slim@sha256:7bec7ddcddeff7975d6ba9b4be7dd6f6b2f55e7491539145e2978f7f97ce9144

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY Projects/employee_management_system/requirements-deploy.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN groupadd --gid 10001 abap && useradd --uid 10001 --gid abap --no-create-home abap
COPY Projects/employee_management_system/ /app/
RUN mkdir -p /app/logs /app/data /app/exports && chown -R abap:abap /app/logs /app/data /app/exports
USER abap
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "deployment:create_application", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers"]
