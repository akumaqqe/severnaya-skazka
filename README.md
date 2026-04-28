# Северная сказка

Учебный Django-проект для дополнительной общеобразовательной программы художественной направленности. Сайт помогает детям 6-11 лет знакомиться с северной народной культурой, участвовать в голосованиях, сохранять результаты обучения и видеть свой рейтинг.

## Возможности

### Для ученика

- регистрация и вход;
- просмотр актуальных голосований;
- участие в голосовании без повторных голосов в одном опросе;
- добавление, изменение и удаление своих учебных результатов;
- просмотр личного кабинета;
- просмотр личного и общего рейтинга;
- автоматическое добавление 1 балла в рейтинг за участие в каждом голосовании.

### Для администратора

- вход через стандартную Django Admin;
- управление голосованиями и вариантами ответов;
- просмотр учеников и их результатов;
- просмотр рейтинга;
- отчёты по успешному прохождению программы;
- статистика по голосованиям;
- отдельные staff-страницы для управления опросами и отчётами.

## Стек

- Python 3.x
- Django 4.2
- MySQL для разработки через переменные окружения
- PostgreSQL для продакшена и Render
- Whitenoise для статических файлов
- DBeaver для работы с БД

## Структура проекта

```text
.
├── core/
├── folk_school/
├── static/
├── templates/
├── .env.example
├── manage.py
├── render.yaml
└── requirements.txt
```

## Установка

```bash
cd <папка_проекта>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Для Render в репозиторий добавлен файл `.python-version` со значением `3.12`, чтобы сервис не использовал слишком новую версию Python по умолчанию.

## Настройка окружения

1. Скопируйте пример:

```bash
cp .env.example .env
```

2. Заполните переменные.

### Настройка MySQL для разработки

В `.env` укажите, например:

```env
DB_ENGINE=mysql
DB_NAME=folk_school
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Именно MySQL считается основной базой для разработки по ТЗ.

### Настройка PostgreSQL

Для локального PostgreSQL:

```env
DB_ENGINE=postgresql
DB_NAME=folk_school
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

Для Render удобнее использовать:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME
DEBUG=False
```

Только для быстрой локальной smoke-проверки можно временно переключить `.env` на `DB_ENGINE=sqlite`, но это не основная dev-конфигурация проекта.

## Миграции

```bash
python manage.py makemigrations
python manage.py migrate
```

## Создание суперпользователя

```bash
python manage.py createsuperuser
```

## Запуск сервера

```bash
python manage.py runserver
```

Сайт будет доступен по адресу [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Как пользоваться сайтом

1. Зарегистрируйте ученика через страницу регистрации.
2. Войдите в личный кабинет.
3. Просматривайте активные голосования и голосуйте.
4. Добавляйте учебные результаты, чтобы они сразу попадали в общий рейтинг.
5. Участвуйте в голосованиях: каждое участие добавляет 1 балл в личный рейтинг.
6. Для управления сайтом используйте `/admin/` или staff-страницы:
   - `/reports/`
   - `/management/polls/`

## Работа с DBeaver

- создайте подключение к MySQL или PostgreSQL;
- используйте параметры из файла `.env`;
- после подключения можно просматривать таблицы `core_profile`, `core_poll`, `core_choice`, `core_vote`, `core_learningresult`.
- `core_profile.total_rating` хранит сумму баллов за задания и бонусных баллов за голосования.

## Деплой на Render

Проект подготовлен к размещению через `render.yaml`.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/akumaqqe/severnaya-skazka)

### Что такое Render через Git

Render — это облачная платформа, которая умеет брать ваш проект прямо из Git-репозитория и запускать его как сайт.

Как это работает:

1. Вы загружаете проект в GitHub или другой Git-репозиторий.
2. В Render подключаете этот репозиторий.
3. Render сам скачивает код из Git.
4. Потом Render выполняет команды сборки:
   - устанавливает зависимости;
   - применяет миграции;
   - собирает статические файлы.
5. После этого Render запускает Django через `gunicorn`.
6. Когда вы пушите новые изменения в Git, Render может автоматически заново развернуть сайт.

Проще говоря, “Render через Git” означает:
- код хранится в Git;
- деплой запускается из этого репозитория;
- обновление сайта происходит после `git push`.

### Что уже настроено

- `gunicorn` добавлен в зависимости;
- `whitenoise` раздаёт статические файлы;
- `DATABASE_URL` поддерживается для PostgreSQL;
- `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` умеют подхватывать `RENDER_EXTERNAL_HOSTNAME`;
- версия Python для Render зафиксирована;
- `collectstatic` и `migrate` вынесены в pre-deploy команду.
- в `render.yaml` сразу описаны Web Service и PostgreSQL база данных;
- для быстрого старта указан `free` plan для веб-сервиса и базы данных.

### Автоматический деплой через Git

1. Загрузите проект в Git-репозиторий.
2. Создайте новый Web Service на Render из репозитория.
3. Render прочитает `render.yaml`.
4. После первого деплоя создайте суперпользователя через Shell на Render:

```bash
python manage.py createsuperuser
```

### Если настраивать вручную

- Build Command:

```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

- Start Command:

```bash
gunicorn folk_school.wsgi:application
```

## ER-диаграмма

```mermaid
erDiagram
    USER ||--|| PROFILE : has
    USER ||--o{ VOTE : gives
    USER ||--o{ LEARNING_RESULT : receives
    POLL ||--o{ CHOICE : contains
    POLL ||--o{ VOTE : collects
    CHOICE ||--o{ VOTE : selected_in

    PROFILE {
        int id
        int age
        string class_group
        int total_rating
        datetime registered_at
    }

    POLL {
        int id
        string title
        text description
        datetime created_at
        datetime end_date
        boolean is_active
    }

    CHOICE {
        int id
        int poll_id
        string text
        int votes_count
    }

    VOTE {
        int id
        int user_id
        int poll_id
        int choice_id
        datetime voted_at
    }

    LEARNING_RESULT {
        int id
        int user_id
        string stage_title
        int points
        boolean is_successful
        datetime created_at
    }
```

## Проверка проекта

После установки зависимостей можно выполнить:

```bash
python manage.py test
python manage.py check
```
