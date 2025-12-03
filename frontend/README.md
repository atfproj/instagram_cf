# Instagram Content Factory - Frontend

Веб-интерфейс для управления Instagram Content Factory.

## Технологии

- **React 18** - UI библиотека
- **Vite** - Сборщик и dev-сервер
- **React Router** - Маршрутизация
- **React Query** - Управление состоянием и кэширование API запросов
- **Tailwind CSS** - Стилизация
- **Lucide React** - Иконки
- **Axios** - HTTP клиент

## Установка

```bash
cd frontend
npm install
```

## Запуск

```bash
# Development режим
npm run dev

# Production сборка
npm run build

# Preview production сборки
npm run preview
```

Приложение будет доступно на `http://localhost:3001`

## Настройка

Создайте файл `.env` в корне `frontend/`:

```env
VITE_API_URL=http://localhost:8009
```

## Структура проекта

```
frontend/
├── src/
│   ├── api/              # API клиенты
│   ├── components/       # Переиспользуемые компоненты
│   ├── pages/           # Страницы приложения
│   ├── App.jsx          # Главный компонент
│   ├── main.jsx         # Точка входа
│   └── index.css        # Глобальные стили
├── index.html
├── package.json
└── vite.config.js
```

## Страницы

- **Dashboard** (`/dashboard`) - Общая статистика и обзор
- **Accounts** (`/accounts`) - Управление Instagram аккаунтами
- **Groups** (`/groups`) - Управление группами аккаунтов
- **Posts** (`/posts`) - Создание и управление постами
- **Proxies** (`/proxies`) - Управление прокси серверами

## API интеграция

Все API запросы идут через прокси на `http://localhost:8009/api` (настроено в `vite.config.js`).

API клиенты находятся в `src/api/`:
- `accounts.js` - Работа с аккаунтами
- `groups.js` - Работа с группами
- `posts.js` - Работа с постами
- `proxies.js` - Работа с прокси

