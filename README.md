# Автоматизоване тестування та розгортання Python-сервісу

## 1. Запуск застосунку

Встановлення залежностей:

```bash
python -m pip install -r requirements-dev.txt
```

Створення файлу налаштувань та запуск Docker-контейнера:

```bash
cp .env.example .env
docker compose up --build -d
```

Для PowerShell команда створення `.env`:

```powershell
Copy-Item .env.example .env
```

## 2. Перевірка

Перевірка стану сервісу та його версії:

```bash
curl --max-time 3 http://localhost:5000/health
curl --max-time 3 http://localhost:5000/version
```

Запуск модульних тестів:

```bash
python -m pytest -v tests/test_app.py
```

Інфраструктурні тести Testinfra запускаються в Linux-середовищі з Docker:

```bash
python -m pytest -v --hosts=docker://pr6-app tests/test_infra.py
```

Перегляд стану контейнера та журналів:

```bash
docker compose ps
docker compose logs app
```

## 3. Розгортання та відкат

Розгортання нової версії виконується автоматично через GitHub Actions після успішних перевірок і злиття змін у гілку `main`.

Якщо перевірка `/health` завершується помилкою, скрипт `scripts/deploy.sh` відновлює попередню конфігурацію та Docker-образ, після чого повторно перевіряє сервіс. Невдале розгортання залишається позначеним як помилка.

Для ручного відкату до попередньої конфігурації на Ubuntu VM:

```bash
cd /home/pr6user/pr6-deploy
cp .env.previous .env
docker compose --env-file .env -f compose.deploy.yaml up -d --no-build --force-recreate
curl --fail --max-time 3 http://localhost:5000/health
```

Ручний відкат можливий, якщо файл `.env.previous` і відповідний попередній Docker-образ збережені.

