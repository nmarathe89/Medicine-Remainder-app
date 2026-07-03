# Two-stage build. Stage 1 compiles the Vite bundle; stage 2 is the runtime
# image that just serves the built artifacts + Express SSR.
FROM node:22-slim AS builder

WORKDIR /app
COPY package.json ./
# Prefer `npm ci` when a lockfile exists; fall back for the initial setup.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY client ./client
COPY vite.config.js ./
COPY server ./server
RUN npm run build

# --- runtime image -----------------------------------------------------------
FROM node:22-slim

ENV NODE_ENV=production
WORKDIR /app

# Only production runtime deps.
COPY package.json ./
RUN if [ -f package-lock.json ]; then npm ci --omit=dev; else npm install --omit=dev; fi \
    && useradd --create-home --uid 1001 appuser

COPY --from=builder /app/dist ./dist
COPY server ./server

USER appuser
EXPOSE 3000
CMD ["node", "server/index.js"]
