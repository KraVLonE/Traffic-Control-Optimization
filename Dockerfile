# Stage 1: Build Frontend
FROM node:18-alpine as build
WORKDIR /app/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy source code and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Setup Backend
FROM python:3.9-slim
WORKDIR /app

# Install system dependencies if needed (e.g. for numpy/matplotlib)
# RUN apt-get update && apt-get install -y ...

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy trained model (if it exists, otherwise comment this out)
COPY q_table.pkl .

# Copy built frontend static files from Stage 1
COPY --from=build /app/frontend/dist /app/frontend/dist

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
