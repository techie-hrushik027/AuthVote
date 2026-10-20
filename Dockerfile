FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Keep the existing layout because app.py locates Frontend relative to its file.
COPY Backend/ /app/Backend/
COPY Frontend/ /app/Frontend/

RUN addgroup --system app && adduser --system --ingroup app app
USER app

WORKDIR /app/Backend

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
