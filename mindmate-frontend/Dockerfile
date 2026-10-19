# MindMate frontend: build with Vite, serve with nginx.
#   docker build --build-arg VITE_API_BASE_URL=https://api.example.com -t mindmate-frontend mindmate-frontend
#   docker run -p 8080:80 mindmate-frontend
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# VITE_* values are baked in at build time. Leave empty to build the offline mock mode.
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1/healthz || exit 1
