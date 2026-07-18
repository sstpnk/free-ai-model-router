# Free AI Model Router

Ежедневный ETL-процесс для обнаружения, проверки, оценки и ранжирования бесплатных API-моделей, пригодных для качественной работы с кодом. Генерирует проверяемый пример конфигурации LiteLLM.

## Быстрый старт

```bash
# Установка
pip install -e ".[dev]"

# Полный цикл
python -m free_ai_model_router run-all

# Отдельные шаги
python -m free_ai_model_router collect
python -m free_ai_model_router discover
python -m free_ai_model_router verify
python -m free_ai_model_router rank
python -m free_ai_model_router generate
python -m free_ai_model_router report
```

## Docker

```bash
docker build -t free-ai-model-router .
docker run --env-file .env free-ai-model-router
```

## Структура

- `config/` — YAML-конфигурация (провайдеры, источники, скоринг, переопределения)
- `src/free_ai_model_router/` — исходный код
- `data/` — кеш, нормализованные данные, история
- `output/` — сгенерированные конфиги (`litellm-config-sample.yaml`)
- `reports/` — отчёты (models.md, changes.md, sources-health.md)

## Лицензия

MIT
