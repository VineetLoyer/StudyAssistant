ARG PY_BASE=python:3.10-slim-bookworm
ARG CACHEBUST=3
FROM ${PY_BASE}

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libgomp1 libglib2.0-0 libgl1 tzdata wkhtmltopdf && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt

# make sure pip itself is fresh, then install exactly what's in requirements
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PORT=8080
EXPOSE 8080
CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
