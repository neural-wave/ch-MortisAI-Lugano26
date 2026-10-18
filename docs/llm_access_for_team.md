# Доступ к нашей LLM (Qwen3.8-27B на vast.ai) из Python

Модель: `Qwen/Qwen3.8-27B`, сервер vLLM с OpenAI-совместимым API.
Адрес и токен — у Назара. **Токен — это пароль: не публикуй, не коммить в git, не вставляй в общий чат.**

## 1. Окружение (один раз)

Нужен Python 3.10+ с современным OpenSSL. Проверка:
```bash
python3 -c "import ssl; print(ssl.OPENSSL_VERSION)"    # нужен OpenSSL 3.x
```
Если там `LibreSSL 2.x` (системный Python macOS) — поставь Python из Homebrew: `brew install python`.

В папке проекта:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openai httpx
```

## 2. Адрес и токен

Создай в папке проекта файл `.env` (и добавь `.env` в `.gitignore`!):
```bash
cat > .env <<'EOF'
export VAST_URL="http://<IP>:<port>"   # the address of the running instance (vast.ai console)
export VAST_TOKEN="ТОКЕН_ОТ_НАЗАРА"
EOF
```
В каждом новом терминале:
```bash
source .venv/bin/activate && source .env
```

Важно:
- адрес именно **http://**, не https (на https будет ошибка `WRONG_VERSION_NUMBER`);
- если инстанс перезапускали, внешний порт мог измениться — уточни у Назара;
- если сервер не отвечает — скорее всего, инстанс остановлен ради экономии, напиши Назару.

## 3. Проверка

```bash
curl $VAST_URL/v1/models -H "Authorization: Bearer $VAST_TOKEN"
```
Должен вернуться JSON с `"id":"Qwen/Qwen3.8-27B"`.

## 4. Клиент на Python

```python
import os, httpx
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["VAST_URL"] + "/v1",
    api_key=os.environ["VAST_TOKEN"],
    http_client=httpx.Client(timeout=900),   # размышления могут идти минуты
)
MODEL = "Qwen/Qwen3.8-27B"


def ask(prompt: str, n: int = 1) -> list[str]:
    """Основной режим: модель думает со средней глубиной. Для логики, кода, гипотез."""
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        n=n,                          # n>1 = несколько независимых вариантов (best-of-N)
        max_tokens=16000,             # место под размышления + ответ
        temperature=1.0, top_p=0.95,
        reasoning_effort="medium",
        extra_body={"top_k": 20},
    )
    return [c.message.content for c in r.choices]


def ask_fast(prompt: str) -> str:
    """Без размышлений: быстро, для простых технических действий (переформатировать, извлечь)."""
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0.7, top_p=0.8,
        extra_body={"top_k": 20, "presence_penalty": 1.5,
                    "chat_template_kwargs": {"enable_thinking": False}},
    )
    return r.choices[0].message.content


if __name__ == "__main__":
    print(ask("236.25 * 0.04 stored as 9.45 — which rounding rule? Answer briefly.")[0])
```

## 5. Что нужно знать о режимах

| Режим | Когда | Скорость |
|---|---|---|
| `reasoning_effort="medium"` | **по умолчанию**: логика, гипотезы, код | ~65 ток/с, обычно 5–30 с |
| без размышлений (`ask_fast`) | простые действия | секунды; на логике хуже |
| `reasoning_effort="xhigh"` | только если medium не справился; ставь `max_tokens` 32000 | может думать минутами |

- Без явного `reasoning_effort` модель думает на **максимуме** и может съесть весь лимит токенов, вернув
  пустой ответ (`content=None`, `finish_reason="length"`). Всегда указывай режим.
- Размышления модели лежат отдельно: `message.reasoning_content` (или `message.reasoning`), ответ — в `message.content`.
- Параллельные запросы почти не замедляют друг друга — `n=8` занимает примерно столько же времени, сколько `n=1`
  (ожидание; на практике выигрыш MTP при параллельной нагрузке меньше, см. ниже).
- Аренда стоит ~$1.4/ч, бюджет ограничен — не гоняй бесконечные циклы без нужды.

## 6. Как развёрнут сервер (контекст для твоей LLM)

- **Модель:** `Qwen/Qwen3.8-27B` — dense 27B, Apache 2.0, полная точность BF16 (~56 ГБ весов), без квантования.
  Бенчмарки (от Qwen): SWE-bench Pro 61.7, LiveCodeBench v6 90.3, GPQA Diamond 89.2, HLE 30.8.
  Выбрана как самая сильная по логике/коду open-weight модель в бюджете; Artificial Analysis Index 52
  (выше, чем у более крупной Qwen3.8-Flash-Next — 40).
- **Железо:** vast.ai, 1× NVIDIA RTX PRO 6000 Blackwell Workstation (96 ГБ VRAM), Испания, надёжность 99.94 %.
- **Сервер:** vLLM 0.27.1 (образ `vllm/vllm-openai:v0.27.1-cu129`, шаблон «Qwen3.8 27B, vLLM» из vast.ai Model Library).
  Внутри слушает `127.0.0.1:18000`, наружу через прокси с проверкой токена: порт 8000 → внешний порт инстанса.
  Протокол **HTTP**, не HTTPS.
- **Аргументы vLLM:** `--max-num-seqs 256 --enable-auto-tool-choice --tool-call-parser qwen3_coder
  --reasoning-parser qwen3 --trust-remote-code` + **MTP** `--speculative-config '{"method":"mtp","num_speculative_tokens":3}'`.
- **Контекст:** до 262 144 токенов на запрос; KV-кеш ~532 000 токенов суммарно на все параллельные запросы
  (≈2 запроса с полным контекстом одновременно, коротких — десятки).
- Отдельно предусмотрены: tool calling (парсер `qwen3_coder`), отделение размышлений (`reasoning_content`).
  Модель также понимает изображения (vision), но мы это не используем.

## 7. Результаты наших тестов

Тестовый вопрос: «A legacy insurance system computes commission = premium * rate. Premium 236.25, rate 0.04,
stored result 9.45. Which rounding rule explains it? Answer briefly.» Правильный ответ: округление не нужно,
236.25 × 0.04 = 9.45 ровно (вопрос с подвохом — проверяет, не придумает ли модель лишнее).

### До включения MTP

| Режим | Время | Токены | finish | Результат |
|---|---|---|---|---|
| по умолчанию (размышления xhigh), `max_tokens=4000` | 166 с | 4000 | length | ❌ `content=None` — весь лимит ушёл на размышления |
| без размышлений, `max_tokens=1000` | 34 с | 1000 | length | ❌ рассуждает хаотично прямо в ответе, путается (float, truncation…), не закончил |
| размышления **medium**, `max_tokens=16000` | 18.8 с | 546 | stop | ✅ «No rounding is required. 236.25 × 0.04 = 9.45 exactly» |

Скорость генерации: **~24–29 токенов/с** на один запрос.

### После включения MTP

| Режим | Время | Токены | finish | Результат |
|---|---|---|---|---|
| без размышлений | 2.2 с | 69 | stop | ✅ коротко и верно («exact mathematical product… None») |
| размышления **medium** | 5.6 с | 375 | stop | ✅ «None — no rounding is needed… 9.45 exactly» |

- Скорость: **~29 → ~67 токенов/с** (≈2.3× быстрее), качество ответов не изменилось.
- Метрики MTP (`/metrics` vLLM): черновиков 149, черновых токенов 447, принято 297 → **~66 % принятия**,
  в среднем ~2 из 3 догадок принимаются → ~3 токена за проход основной модели.
- Разница в режиме «без размышлений» между двумя прогонами (длинный путаный vs короткий верный) — во многом
  случайность сэмплинга. Для логических задач всё равно используем medium.

### Выводы из тестов

1. **Всегда задавай `reasoning_effort`.** По умолчанию модель думает на максимуме (xhigh) и на простых вопросах
   «передумывает» до исчерпания лимита.
2. **Основной режим — medium:** быстрее и надёжнее, чем без размышлений; поймал подвох в вопросе.
3. **Без размышлений** — только для механических задач (форматирование, извлечение кода).
4. **xhigh** — для действительно трудных случаев, с `max_tokens` 16–32 тыс. и запасом по таймауту.
5. Проверяй `finish_reason`: `length` = не хватило токенов (увеличь `max_tokens` или понизь глубину).

## 8. Известные проблемы и решения

| Симптом | Причина / решение |
|---|---|
| curl: `tlsv1 alert protocol version` или `--tlsv1.3 not found built-in` | системный curl macOS (LibreSSL) + https. Используй **http://** |
| Python: `SSL: WRONG_VERSION_NUMBER` | обращение по https к HTTP-порту → поменяй на **http://** |
| `ModuleNotFoundError: httpx` / `externally-managed-environment` | ставь пакеты в venv (раздел 1) |
| `401 Unauthorized` | неверный токен / нет заголовка `Authorization: Bearer ...` |
| `Connection refused` / таймаут подключения | инстанс остановлен или сменился порт — спроси Назара |
| `content=None`, `finish_reason="length"` | модель не уложилась в `max_tokens` — см. выводы выше |
| Quick Tunnel (https trycloudflare) | работает, но ссылка меняется при рестарте и Cloudflare рвёт запросы > ~100 с — для долгих размышлений не подходит |

## 9. Как мы планируем использовать LLM (для понимания задачи)

Хакатон Lifeware: восстановить скрытые правила legacy-системы страхования по данным и выдать их как
детерминированный Python-код. LLM **не считает ответы** — она предлагает новые «кирпичики» (функции-гипотезы:
способ округления, сдвиг даты, расчёт возраста…), когда автоматический перебор по словарю застрял.
Каждую идею строго проверяет верификатор на всех строках данных; принимается только то, что повышает точность
на отложенных полисах. Поэтому выгодно просить **несколько вариантов** (`n=5..8`) в режиме medium и давать
модели компактный отчёт об ошибках + 3–5 примеров уже принятых кирпичиков. Ответ просить строго в блоке
```python``` с заданной сигнатурой функции. Все пары «запрос → кандидат → принят/нет» логировать в
`logs/llm_proposals.jsonl`.
