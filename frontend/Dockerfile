# ---- build stage ----
FROM node:22-slim AS builder
WORKDIR /app

# NEXT_PUBLIC_* vars are baked into the bundle at build time, not settable at runtime
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# Where next.config.ts proxies /docs/* on the server side. Defaults to NEXT_PUBLIC_API_URL; only
# docker compose sets it, because there "localhost:8000" means the frontend container itself.
ARG INTERNAL_API_URL
ENV INTERNAL_API_URL=$INTERNAL_API_URL

COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- runtime stage ----
FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
