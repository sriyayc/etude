FROM python:3.13

ARG PORT=8080
ARG API_URL
ENV PORT=$PORT \
    REFLEX_API_URL=${API_URL:-http://localhost:$PORT} \
    REFLEX_REDIS_URL=redis://localhost \
    PYTHONUNBUFFERED=1

RUN apt-get update -y && apt-get install -y caddy redis-server && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN reflex init

RUN test -f reflex.lock/bun.lock && cp reflex.lock/bun.lock reflex.lock/package.json .web/ || true

RUN mkdir -p /srv \
    && reflex export --frontend-only --no-zip \
    && mv .web/build/client/* /srv/ \
    && rm -rf /srv/.env .web

STOPSIGNAL SIGKILL

EXPOSE $PORT

CMD caddy start --config Caddyfile --adapter caddyfile && \
    redis-server --daemonize yes && \
    exec reflex run --env prod --backend-only