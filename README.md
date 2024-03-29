# hw05_final

Проект социальной сети Yatube, сделанный в рамках Яндекс.Практикума, выполнен на Django 2.2. В проекте можно регистрироваться, публиковать и комментировать посты, добавлять к ним изображения и подписываться на других пользователей.

## Стек технологий:
python 3, Django 2.2, SQLite, html, bootstrap, unittest

## Для запуска проекта:
1. Проверьте установлен ли интерпретатор Python.
2. Клонируйте репозиторий и перейдите в папку проекта, для этого в консоли наберите:
    ```
    git clone https://github.com/ValentinDevPy/hw05_final/hw05_final
    cd hw05_final
    ```
3. Создайте и активируйте виртуальное окружение:
    ```
    python3 -m venv venv
    source ./venv/bin/activate
    ```
4. Установите зависимости:
    ```
    pip install -r requirements.txt
    ```
5. Выполните миграции:
    ```
    python manage.py migrate
    ```
6. Соберите статику
    ```
    python manage.py collectstatic
    ```
8. Для запуска приложения используйте:
    ```
    python manage.py runserver
    ```
8. Приложение доступно по адресу: `http://127.0.0.1:8000/`.
