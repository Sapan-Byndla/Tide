# TIDE frontend image (Phase 0).
#
# Runs the Next.js dev server. Build context is the `frontend/` directory.
# Production multi-stage build is added in a later phase.

FROM node:22-slim AS base

ENV NODE_ENV=development
WORKDIR /app

# Install dependencies first for layer caching.
COPY package.json ./
# package-lock.json is optional in Phase 0; use `npm install` for resilience.
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
