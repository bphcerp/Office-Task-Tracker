# syntax=docker/dockerfile:1
FROM node:22-alpine AS base
RUN corepack enable
WORKDIR /app

# ---- dependencies -----------------------------------------------------------
FROM base AS deps
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# ---- development ------------------------------------------------------------
FROM base AS dev
ENV PATH="/app/node_modules/.bin:$PATH"
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
# Astro SSR fetches the backend via BACKEND_UPSTREAM (see src/lib/api.ts).
ENV BACKEND_UPSTREAM=http://backend:8000
EXPOSE 4321
CMD ["pnpm", "dev", "--host", "0.0.0.0"]

# ---- build ------------------------------------------------------------------
FROM deps AS build
COPY . .
RUN pnpm build

# ---- production -------------------------------------------------------------
FROM node:22-alpine AS prod
RUN corepack enable
WORKDIR /app
ENV NODE_ENV=production
ENV BACKEND_UPSTREAM=http://backend-prod:8000
COPY --from=build /app/dist ./dist
EXPOSE 4321
CMD ["node", "dist/server/entry.mjs"]
