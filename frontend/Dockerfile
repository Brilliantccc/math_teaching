# ============================================
# 前端 Dockerfile - Vue 3 + Nginx
# ============================================

# 构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

# 安装依赖
COPY package.json package-lock.json* ./
RUN npm ci

# 复制源代码并构建
COPY . .
RUN npm run build

# 运行阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
