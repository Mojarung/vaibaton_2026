# Инструкция для жюри

Все примеры ниже выполнены на сервисе, поднятом по README (`docker compose up -d --build --wait`,
`.env` скопирован из `.env.example`). Ответы в примерах настоящие, сокращены только длинные поля.

```bash
URL=http://localhost:8080   # TODO: адрес публичного стенда, если он будет
```

В Windows Git Bash кириллица в аргументе `-d` портится при передаче в curl. Там надёжнее
положить тело в UTF-8 файл и отправить его через `--data-binary @body.json`.

## 1. Демо-страница

Откройте `$URL/demo`. На странице:

1. Выберите пример текста или вставьте свой. Можно выбрать систему-потребителя: `default`, `crm`
   (ключ `change-me-crm`) или `support_bot` (ключ `change-me-support`).
2. «Замаскировать» показывает текст, который уйдёт наружу, с подсвеченными масками, и таблицу
   найденных значений с позициями. Значения в таблице вычисляет браузер из вашего текста, сервер
   их не возвращает.
3. В поле «Восстановление» ответ можно переписать так, как это сделала бы LLM: переставить
   плейсхолдеры или повторить их. «Демаскировать» вернёт исходные значения.
4. «Через LLM-прокси» отправляет текст в `/v1/chat/completions`. Слева видно, что получила модель,
   ниже ответ клиенту после восстановления.
5. «Контракт /process» делает два вызова автопроверки с одним `payload_id` и сверяет результат
   с исходником посимвольно.
6. Внизу раз в 2 секунды обновляются RPS, TPS и перцентили latency по всем воркерам.

## 2. Маскирование и демаскирование через API

Контракт автопроверки: первый вызов маскирует, второй с тем же `payload_id` демаскирует.

```bash
curl -s $URL/process -H 'Content-Type: application/json' \
  -d '{"payload": "Клиент Иванов Иван, паспорт 4509 123456", "payload_id": "demo-1"}'
# {"result":"Клиент [ФИО_1], паспорт [ПАСПОРТ_1]"}

curl -s $URL/process -H 'Content-Type: application/json' \
  -d '{"payload": "Клиент [ФИО_1], паспорт [ПАСПОРТ_1]", "payload_id": "demo-1"}'
# {"result":"Клиент Иванов Иван, паспорт 4509 123456"}
```

API для систем-потребителей возвращает `session_id` и позиции. Демаскировать можно и ответ LLM,
в котором токены переставлены:

```bash
curl -s $URL/v1/mask -H 'Content-Type: application/json' \
  -d '{"text": "Клиент Петров Пётр Петрович, карта 4276 3800 1234 5678, CVV 123, тел. +7 916 555-12-34"}'
# {"masked": "Клиент [ФИО_1], карта [НОМЕР_КАРТЫ_1], CVV [CVV_1], тел. [ТЕЛЕФОН_1]",
#  "session_id": "44683e101fa5192d9ac4733632eb6fb2",
#  "entities": [{"type": "PERSON", "subtype": null, "token": "[ФИО_1]", "start": 7, "end": 14,
#                "source_start": 7, "source_end": 27}, ...],
#  "counts": {"PERSON": 1, "BANK_CARD": 1, "CVV": 1, "PHONE": 1},
#  "elapsed_ms": ...}

curl -s $URL/v1/unmask -H 'Content-Type: application/json' \
  -d '{"text": "Уважаемый [ФИО_1], карта [НОМЕР_КАРТЫ_1] перевыпущена.", "session_id": "44683e101fa5192d9ac4733632eb6fb2"}'
# {"text": "Уважаемый Петров Пётр Петрович, карта 4276 3800 1234 5678 перевыпущена.", ...}
```

`start`/`end` указывают на токен в маске, `source_start`/`source_end` на значение в исходном тексте.

## 3. LLM-прокси

Без `LLM_BASE_URL` модуль отвечает демо-ответом вместо внешней модели. С заголовком
`X-Pii-Debug: 1` в ответ добавляется поле `pii_guard` с тем, что ушло в модель:

```bash
curl -s $URL/v1/chat/completions -H 'Content-Type: application/json' -H 'X-Pii-Debug: 1' \
  -d '{"messages": [{"role": "user", "content": "Клиент Петров Пётр Петрович, карта 4276 3800 1234 5678, CVV 123, тел. +7 916 555-12-34"}]}'
# "pii_guard": {"sent_to_llm": [{"role": "user",
#     "content": "Клиент [ФИО_1], карта [НОМЕР_КАРТЫ_1], CVV [CVV_1], тел. [ТЕЛЕФОН_1]"}], ...}
# "content": "Демо-ответ: внешняя LLM не настроена (LLM_BASE_URL пуст). Обращение обработано.
#     Данные клиента из запроса: 123, 4276 3800 1234 5678, +7 916 555-12-34, Петров Пётр Петрович."
```

Чтобы подключить AlfaGen, впишите в `.env` `LLM_BASE_URL=https://alfagen.alfabank.ru/continue-dev/v1`
и `LLM_API_KEY`, затем `docker compose up -d`.

## 4. Разные политики для разных систем

Один и тот же текст, три системы из `config/systems.yaml`:

| Система | Заголовки | Результат |
|---|---|---|
| `default` | без заголовков | `Клиент [ФИО_1], карта [НОМЕР_КАРТЫ_1], CVV [CVV_1], тел. [ТЕЛЕФОН_1]` |
| `crm` | `X-System-Id: crm`, `X-Api-Key: change-me-crm` | `Клиент Соколов Николай Александрович, карта 4276********5678, CVV 717, тел. +7 909 338-01-03` |
| `support_bot` | `X-System-Id: support_bot`, `X-Api-Key: change-me-support` | маска как у `default`, но `session_id: null`: демаскирование запрещено |

У `crm` синтетика подставляется вместо значений, а карта открыта частично (`type_modes`).
Синтетические значения тоже восстанавливаются через `/v1/unmask`.

Правило по комбинации у `support_bot`: PIN и CVV маскируются только рядом с номером карты.

```bash
curl -s $URL/v1/mask -H 'X-System-Id: support_bot' -H 'X-Api-Key: change-me-support' \
  -H 'Content-Type: application/json' -d '{"text": "PIN 4321"}'
# {"masked": "PIN 4321", "session_id": null, "entities": [], ...}
```

Отказы:

| Запрос | Ответ |
|---|---|
| `X-System-Id: analytics` (система выключена) | `403 {"error": "system_disabled", "message": "Система отключена"}` |
| `X-System-Id: crm` с неверным ключом | `401 {"error": "invalid_api_key", "message": "Неверный ключ API"}` |
| `support_bot` вызывает `/v1/unmask` | `403`: демаскирование для системы запрещено |

Политику можно поменять на лету: правкой `config/systems.yaml` или через админ-API. Ответ
админ-API содержит итоговый список типов системы: `{"id": "newbot", "types": ["EMAIL", "PHONE"]}`.

```bash
curl -s -X PUT $URL/admin/systems/newbot -H 'X-Admin-Key: change-me-admin' \
  -H 'Content-Type: application/json' -d '{"entity_types": ["PHONE", "EMAIL"], "mask_mode": "redact"}'
curl -s $URL/v1/mask -H 'X-System-Id: newbot' -H 'Content-Type: application/json' \
  -d '{"text": "Иванов, ivan@mail.ru"}'
# {"masked": "Иванов, [EMAIL]", ...}
```

## 5. Ловушки

```bash
curl -s $URL/v1/mask -H 'Content-Type: application/json' -d '{"text": "Поэт Александр Пушкин родился в Москве. Отделение банка на ул. Ленина, д. 5 работает до 20:00. Горячая линия 8 800 100-00-00. Код ошибки 500-012."}'
# {"masked": "Поэт Александр Пушкин родился в Москве. Отделение банка на ул. Ленина, д. 5 работает до 20:00. Горячая линия 8 800 100-00-00. Код ошибки 500-012.", "entities": [], ...}
```

Та же фраза с клиентом маскируется: «Клиент Александр Пушкин, тел. +7 916 555-12-34» даёт
`Клиент [ФИО_1], тел. [ТЕЛЕФОН_1]`.

## 6. Логи

```bash
docker compose logs -f api
```

На каждый запрос одна JSON-строка `request.done`: маршрут, статус, время, система, направление,
найденные типы ПДн с количеством и время каждого этапа. Значений ПДн в логе нет, в том числе при
ошибках валидации: ответ 422 называет только поле.

```json
{"request_id":"ab34da61c4efbfe6","route":"/v1/mask","status":200,"elapsed_ms":4.321,"system":"default",
 "direction":"mask","entities":{"PERSON":1,"BANK_CARD":1,"PHONE":1},"chars":77,"tokens_in":22,
 "tokens_out":0,"detect_ms":2.167,"mask_ms":0.033,"store_ms":0.437,"event":"request.done",
 "service":"Контур","level":"info","timestamp":"2026-09-22T15:19:49.730636Z"}
```

## 7. Метрики

| Где | Что |
|---|---|
| `GET $URL/stats` | RPS средний и пиковый, TPS, p50/p95/p99, число воркеров и ошибок за 60 секунд |
| `GET $URL/metrics` | Prometheus: `pii_requests_total`, `pii_request_seconds`, `pii_stage_seconds`, `pii_entities_total`, `pii_tokens_total`, `pii_rejected_total`, `pii_degraded_total`, `pii_inflight_requests`, `pii_llm_seconds` |
| `docker compose --profile observability up -d` | Prometheus на :9090, Grafana на :3000, дашборд «Модуль защиты ПДн» без логина |
| `GET $URL/health/ready` | состояние хранилища и LLM: `{"status":"ok","store":{"backend":"redis","ok":true},"llm":{"configured":false,"model":"demo"},"rules":87,"systems_version":1}` |

## 8. Ошибки и деградация

| Ситуация | Поведение |
|---|---|
| Невалидный JSON | `400 {"error": "invalid_json", "message": "Некорректный JSON"}` |
| Нет `payload_id` | `422 {"error": "invalid_request", "message": "Поле payload_id обязательно и должно быть строкой"}` |
| Тело больше `MAX_BODY_BYTES` или текст длиннее `MAX_TEXT_CHARS` | `413` |
| Больше `MAX_CONCURRENT` запросов в работе на воркер | `429` с `Retry-After: 1` |
| Redis недоступен | соответствия пишутся в память воркера, `/health/ready` отвечает `degraded`, растёт `pii_degraded_total{component="redis"}` |
| LLM недоступна или не ответила | `502` или `504` с сообщением «Внешняя LLM недоступна, данные не переданы» |
| Ошибка внутри детектора | весь текст заменяется одной меткой `[СКРЫТО_1]`: лучше потерять смысл, чем отдать ПДн |

## 9. Нагрузка

```bash
RATE=1000 DURATION=60s sh load/run.sh
# одна строка сводки: rps, p50, p95, p99, max, доля ошибок, неточные восстановления
```

Результат пятиминутного прогона при 1000 RPS: факт RPS 968, p50 18,7 мс, p95 232,5 мс, p99 371,0 мс,
ошибок 0%, неточных восстановлений 2.

Сценарий `load/process.js` шлёт пары маска/демаска с одним `payload_id` из 200 соединений и
проверяет посимвольное восстановление. Все прогоны и стенд описаны в [PERFORMANCE.md](PERFORMANCE.md).