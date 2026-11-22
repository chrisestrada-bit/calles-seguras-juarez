# Frontend de Calles Seguras Juárez: compilación con Vite y entrega estática con Nginx.
# Contexto de construcción: frontend/ (ver docker-compose.yml).

# --- Etapa 1: compilación -------------------------------------------------------------------
FROM node:20-alpine AS build

WORKDIR /app

# URL base de la API SIN el sufijo /api/v1: el cliente (src/services/api.ts) ya lo antepone a cada ruta.
# Vite la incrusta en el bundle en tiempo de compilación, por eso es un ARG y no una variable de ejecución.
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

# --- Etapa 2: entrega -----------------------------------------------------------------------
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1
