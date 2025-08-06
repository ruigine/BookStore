# --- Build stage ---
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy source files
COPY . .

# Build the SPA (ensure ssr: false in react-router.config.ts)
RUN npm run build

# --- Serve with Nginx ---
FROM nginx:alpine

# Copy built frontend from builder stage
COPY --from=builder /app/build/client /usr/share/nginx/html

# Copy custom nginx config
COPY default.conf /etc/nginx/conf.d/default.conf

# Expose default HTTP port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]