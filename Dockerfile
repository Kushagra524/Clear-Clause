# ==========================================
# Stage 1: Build the React Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY artifacts/legal-document-analyzer/package.json ./
RUN npm install

COPY artifacts/legal-document-analyzer/ ./
RUN npm run build

# ==========================================
# Stage 2: Production Python Backend
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Install minimal OS dependencies for parsing and ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ ./

# Copy compiled frontend assets from Stage 1 into backend/static
COPY --from=frontend-builder /app/frontend/dist ./static

# Environment settings for Hugging Face Spaces / Render / Railway
ENV PORT=7860
ENV FLASK_PORT=7860
ENV FLASK_HOST=0.0.0.0
ENV APP_ENV=production
ENV USE_RERANKER=false

# Expose default port (7860 for HuggingFace Spaces)
EXPOSE 7860

# Run high-performance production server with gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "300", "--worker-class", "gthread", "--threads", "4"]
