
# Student Management System - Group 05
# React + Vite development container

FROM node:24-alpine

WORKDIR /app

# Install dependencies from lockfile
COPY package.json package-lock.json ./
RUN npm ci

# Copy React source code
COPY . .

EXPOSE 5173

# Start Vite for local Docker demonstration
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
