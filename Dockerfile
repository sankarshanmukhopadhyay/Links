FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir .

EXPOSE 8000
ENV LINKS_HOST=0.0.0.0
ENV LINKS_PORT=8000

CMD ["links", "serve", "--host", "0.0.0.0", "--port", "8000"]
