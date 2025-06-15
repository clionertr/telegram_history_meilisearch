FROM node:20-alpine AS builder
WORKDIR /app

# 安装依赖并构建
COPY package*.json ./

# 使用 npm ci，如果失败则回退到 npm install
RUN npm ci --loglevel warn || npm install --loglevel warn

COPY . .
RUN npm run build

# 使用轻量级容器仅提供静态文件
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# 复制构建产物
COPY --from=builder /app/dist ./dist

# 安装一个轻量级静态文件服务器
RUN npm install -g serve

EXPOSE 5173
# 通过 serve 提供构建后的静态网站
CMD ["serve", "-s", "dist", "-l", "5173"] 