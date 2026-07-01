# Деплой astrology-сервиса на VPS

## Структура
```
docker-compose.yaml
astrology/
  Dockerfile
  requirements.txt
  ephe/                  ← сюда положить .se1 файлы (опционально)
  app/
    __init__.py
    main.py               FastAPI: /jyotish /western /human-design /health
    ephemeris.py          обёртка над pyswisseph
    jyotish_calc.py       сидерические позиции, накшатры, Вимшоттари-даша
    hd_calc.py            ворота→центры→тип→авторитет→профиль
    hd_data.py            таблицы ворот/каналов/центров (проверены поиском)
```

## Запуск

```bash
docker compose up -d --build
```

Первый билд — пара минут (компилирует pyswisseph при отсутствии готового
wheel под архитектуру сервера). Дальше — мгновенный рестарт, ничего не
переустанавливается.

Проверка:
```bash
curl http://localhost:8000/health
# {"status":"ok","ephe_mode":"moshier"}
```

`"moshier"` значит используется встроенный алгоритм (без .se1 файлов) —
точности достаточно для MVP. Если хочешь точность уровня Swiss Ephemeris:

```bash
mkdir -p astrology/ephe
cd astrology/ephe
wget https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1
wget https://www.astro.com/ftp/swisseph/ephe/semo_18.se1
cd ../..
docker compose restart astrology
curl http://localhost:8000/health
# {"status":"ok","ephe_mode":"swisseph"}
```

## Тест на конкретной дате

```bash
curl -X POST http://localhost:8000/human-design \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1988-03-15",
    "birth_time": "08:30",
    "timezone": 3,
    "latitude": 55.7558,
    "longitude": 37.6173
  }'
```

## Важно: Human Design без времени рождения

`/human-design` сознательно возвращает HTTP 400, если `birth_time` —
`UNKNOWN`. Это не баг — ХД крайне чувствителен ко времени: Солнце
проходит ~1° в сутки, и даже часовая погрешность может сдвинуть линию
(шаг линии — 0.9375°, то есть ошибка в 22 минуты времени уже может
сдвинуть линию на единицу). Угадывать здесь хуже, чем отказать.

Джйотиш и Западная астрология при `UNKNOWN` отрабатывают нормально —
возвращают знаки/градусы планет без домов/асцендента, с флагом
`time_sensitive: true`.

## Если архитектура сервера ARM (Oracle Free Tier, некоторые Hetzner)

Dockerfile уже содержит `build-essential` на этот случай — pip
скомпилирует pyswisseph из исходников, если нет готового wheel.
Первый билд будет на 1–2 минуты дольше, дальше без разницы.
