# Гайд: Qwen3.8-27B на vast.ai (как реально развёрнуто)

> Обновлено 2026-10-17 по итогам реального развёртывания. Доступ из Python и результаты тестов —
> в `llm_access_for_team.md`.

## Итоговая конфигурация

| | |
|---|---|
| Модель | `Qwen/Qwen3.8-27B`, BF16 (полная точность, ~56 ГБ) |
| GPU | 1× RTX PRO 6000 Blackwell WS, 96 ГБ, Испания, надёжность 99.94 %, ~$1.375/ч |
| Диск | 150 ГБ (модель лежит в `/workspace/models`) |
| Шаблон | «Qwen3.8 27B, vLLM» из **vast.ai Model Library**, образ `vllm/vllm-openai:v0.27.1-cu129` |
| Ускорение | MTP (спекулятивное декодирование): ~29 → ~67 ток/с, качество не меняется |
| Адрес | `http://<IP>:<внешний порт для 8000>` — **HTTP, не HTTPS** |
| Доступ | заголовок `Authorization: Bearer <токен из Instance Portal>` |

## Развёртывание с нуля (если инстанс пересоздаётся)

1. **Баланс** на vast.ai пополнен (на ~60 ч нужно ~$85–90).
2. Открыть **https://vast.ai/model/qwen38-27b** (Model Library; в разделе Templates поиском не находится) → **Deploy Now**.
3. В открывшемся поиске машин: **Container Size 150 ГБ**, **Reliability ≥ 99 %**, GPU **RTX PRO 6000**,
   Unverified Machines выключено. Смотреть на надёжность и цену; место в «Auto Sort» ничего не значит.
   Медленный ↓ канал влияет только на первое скачивание (~10 мин на ~1 Гбит/с).
4. **Rent.** Удалить лишние инстансы (каждый тарифицируется).
5. Ждать в **LOG**: скачивание образа → модели → компиляция → `Application startup complete` (первый раз ~15 мин).
   Безвредные сообщения: `[ERROR] max_frames … not documented`, предупреждение `HF_TOKEN`, `use_fast deprecated`,
   `[model-ui] Timed out waiting for API` (веб-чат шаблона устал ждать — на API не влияет).
6. **Включить MTP** (Instance Portal → **Jupyter Terminal**):
   ```bash
   [ -f /etc/vllm-args.conf ] && cat /etc/vllm-args.conf        # если файл есть — дописать, а не перезаписать
   cat > /etc/vllm-args.conf <<'EOF'
   --speculative-config '{"method":"mtp","num_speculative_tokens":3}'
   EOF
   # надёжный перезапуск (обычный supervisorctl restart падает с "Address already in use"):
   pkill -f "vllm serve"; pkill -f EngineCore; sleep 5; pkill -9 -f "vllm serve"; pkill -9 -f EngineCore; sleep 3
   supervisorctl start vllm
   until curl -s localhost:18000/health >/dev/null; do echo "loading... $(date +%H:%M:%S)"; sleep 10; done; echo READY
   ```
   Старт с моделью на диске ~4–5 мин. Скрипт `/opt/supervisor-scripts/vllm.sh` дописывает содержимое
   `/etc/vllm-args.conf` в конец команды `vllm serve`.
7. **Проверить MTP:**
   ```bash
   tr '\0' ' ' < /proc/$(pgrep -f "vllm serve" | tail -1)/cmdline | grep -o "speculative.*"
   curl -s localhost:18000/metrics | grep -E "spec_decode_num_(drafts|draft_tokens|accepted_tokens)_total\{"
   ```
   (`ps -eo args` обрезает длинную строку — не годится для проверки.) Было: принято ~66 % черновых токенов.
8. **Адрес и токен:** Instance Portal → карточка **vLLM API** → **Advanced Connection Options**:
   `Port: 8000 → <внешний порт>`, IP. Токен — из ссылки портала (`token=…`).
9. С Mac: `curl http://<IP>:<порт>/v1/models -H "Authorization: Bearer $VAST_TOKEN"` → JSON с моделью.

## Что внутри шаблона (для отладки)

- vLLM запускается supervisor-службой `vllm` (`/etc/supervisor/conf.d/vllm.conf` → `/opt/supervisor-scripts/vllm.sh`).
- Аргументы из env `VLLM_ARGS` (`/etc/environment`):
  `--max-num-seqs 256 --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3
  --trust-remote-code --download-dir /workspace/models --host 127.0.0.1 --port 18000`
  + сложные аргументы из `/etc/vllm-args.conf` (MTP).
- vLLM слушает `127.0.0.1:18000`; наружу — прокси Caddy с проверкой токена (порт 8000 → внешний).
- Контекст 262 144 токенов (по умолчанию модели), KV-кеш ~532 тыс. токенов.
- Логи службы идут в общий лог инстанса (LOG на карточке / Instance Logs в портале), не в файл.
- Полезное в портале: **Jupyter Terminal** (шелл на сервере), **Supervisor** (запуск/остановка служб, напр. `model-ui`
  для веб-чата), **Quick Tunnel** (https-ссылка Cloudflare; меняется при рестарте, рвёт запросы > ~100 с).

## Stop / Start / Destroy

| Действие | GPU | Диск | Что сохраняется |
|---|---|---|---|
| **Stop** | не платишь | ~$0.04/ч | всё: модель, `/etc/vllm-args.conf`, кеш компиляции, токен. Start → vLLM сам стартует с MTP за ~4–5 мин. **Проверь внешний порт** — может смениться. Риск: GPU займут, Start будет ждать → тогда Destroy и пересоздать |
| **Destroy** | нет | нет | ничего — развёртывание с нуля (шаги 2–9), MTP-файл записать заново |

Баланс 0 → инстанс останавливают и могут удалить.

## Типичные ошибки

| Симптом | Причина / решение |
|---|---|
| curl `tlsv1 alert protocol version` / Python `SSL: WRONG_VERSION_NUMBER` | порт работает по **HTTP** — используй `http://` |
| `--tlsv1.3 … not found built-in` | системный curl macOS без TLS 1.3 (и не нужен — см. выше) |
| `OSError: [Errno 98] Address already in use` после рестарта | старый процесс vLLM жив — надёжный перезапуск из шага 6 |
| `vllm EXITED` сразу после `supervisorctl restart` | то же самое |
| `CUDA out of memory` при старте | старый процесс держит память (`nvidia-smi`), добить его |
| `401 Unauthorized` | токен / заголовок `Authorization: Bearer …` |
| `content=None`, `finish_reason=length` | модель не уложилась в `max_tokens` — задавай `reasoning_effort="medium"` |
| Долгая тишина в логе на `CUDA graph capture` | первый запуск компилирует ядра под Blackwell, до ~10 мин — норма |

## LoRA (опционально, в конце)

Шаблоны vast.ai **Unsloth Studio** / **Axolotl** для обучения; в vLLM — `--enable-lora --lora-modules name=/path`
(добавить в `/etc/vllm-args.conf`), в запросах `model="name"`.
