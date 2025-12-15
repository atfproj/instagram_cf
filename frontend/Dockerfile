FROM node:18-alpine

WORKDIR /app

# Копирование package файлов
COPY package*.json ./

# Установка зависимостей
RUN npm install

# Копирование остального кода
COPY . .

EXPOSE 3001

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


