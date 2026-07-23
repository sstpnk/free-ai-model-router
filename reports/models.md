# Отчёт по моделям — Free AI Model Router

*Сгенерировано: 2026-07-23 07:45:31 UTC*

*Источник рейтингов: Artificial Analysis (api)*

## Маршрут (включены в litellm-config-sample.yaml)

| Место | Поставщик | Модель | Качество | Уверенность | Бесплатность | Лимиты | Статус API |
|---|---:|---:|---:|:---:|:---:|---:|:---:|
| 1 | openrouter | cohere/north-mini-code:free | 58.9% |  | verified_free | нет данных
context 256k | success |
| 2 | mistral | mistral-medium | 41.7% |  | account_specific_free | нет данных | success |
| 3 | mistral | mistral-medium-3 | 41.7% |  | account_specific_free | нет данных | success |
| 4 | openrouter | poolside/laguna-s-2.1:free | 18.0% |  | verified_free | нет данных
context 262k | success |
| 5 | openrouter | poolside/laguna-xs-2.1:free | 18.0% |  | verified_free | нет данных
context 262k | rate_limited |
| 6 | openrouter | nvidia/nemotron-3.5-content-safety:free | 18.0% |  | verified_free | нет данных
context 128k | success |
| 7 | openrouter | nvidia/nemotron-3-ultra-550b-a55b:free | 18.0% |  | verified_free | нет данных
context 1000k | success |
| 8 | openrouter | nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | 18.0% |  | verified_free | нет данных
context 256k | success |
| 9 | openrouter | poolside/laguna-m.1:free | 18.0% |  | verified_free | нет данных
context 262k | success |
| 10 | openrouter | google/gemma-4-26b-a4b-it:free | 18.0% |  | verified_free | нет данных
context 262k | success |
| 11 | openrouter | google/gemma-4-31b-it:free | 18.0% |  | verified_free | нет данных
context 262k | rate_limited |
| 12 | openrouter | nvidia/nemotron-3-super-120b-a12b:free | 18.0% |  | verified_free | нет данных
context 262k | success |
| 13 | openrouter | nvidia/nemotron-3-nano-30b-a3b:free | 18.0% |  | verified_free | нет данных
context 256k | success |
| 14 | openrouter | nvidia/nemotron-nano-12b-v2-vl:free | 18.0% |  | verified_free | нет данных
context 128k | success |
| 15 | openrouter | nvidia/nemotron-nano-9b-v2:free | 18.0% |  | verified_free | нет данных
context 128k | success |
| 16 | openrouter | openai/gpt-oss-20b:free | 18.0% |  | verified_free | нет данных
context 131k | success |
| 17 | zai | glm-4.5 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 18 | zai | glm-4.5-air | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 19 | zai | glm-4.6 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 20 | zai | glm-4.7 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 21 | zai | glm-5 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 22 | zai | glm-5-turbo | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 23 | zai | glm-5.1 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 24 | zai | glm-5.2 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 25 | groq | canopylabs/orpheus-v1-english | 18.0% |  | documented_free | нет данных
context 4k | invalid_response |
| 26 | groq | groq/compound-mini | 18.0% |  | documented_free | нет данных
context 131k | success |
| 27 | groq | llama-3.3-70b-versatile | 18.0% |  | documented_free | нет данных
context 131k | success |
| 28 | groq | groq/compound | 18.0% |  | documented_free | нет данных
context 131k | success |
| 29 | groq | qwen/qwen3.6-27b | 18.0% |  | documented_free | нет данных
context 131k | success |
| 30 | groq | llama-3.1-8b-instant | 18.0% |  | documented_free | нет данных
context 131k | success |
| 31 | groq | openai/gpt-oss-20b | 18.0% |  | documented_free | нет данных
context 131k | success |
| 32 | groq | canopylabs/orpheus-arabic-saudi | 18.0% |  | documented_free | нет данных
context 4k | invalid_response |
| 33 | groq | openai/gpt-oss-120b | 18.0% |  | documented_free | нет данных
context 131k | success |
| 34 | groq | allam-2-7b | 18.0% |  | documented_free | нет данных
context 4k | success |
| 35 | mistral | mistral-medium-2505 | 18.0% |  | account_specific_free | нет данных | success |
| 36 | mistral | mistral-medium-2508 | 18.0% |  | account_specific_free | нет данных | success |
| 37 | mistral | open-mistral-nemo | 18.0% |  | account_specific_free | нет данных | success |
| 38 | mistral | open-mistral-nemo-2407 | 18.0% |  | account_specific_free | нет данных | success |
| 39 | mistral | mistral-tiny-2407 | 18.0% |  | account_specific_free | нет данных | success |
| 40 | mistral | mistral-tiny-latest | 18.0% |  | account_specific_free | нет данных | success |
| 41 | mistral | codestral-2508 | 18.0% |  | account_specific_free | нет данных | success |
| 42 | mistral | codestral-latest | 18.0% |  | account_specific_free | нет данных | success |
| 43 | mistral | mistral-code-latest | 18.0% |  | account_specific_free | нет данных | success |
| 44 | mistral | mistral-code-fim-latest | 18.0% |  | account_specific_free | нет данных | success |
| 45 | mistral | devstral-2512 | 18.0% |  | account_specific_free | нет данных | success |
| 46 | mistral | devstral-medium-latest | 18.0% |  | account_specific_free | нет данных | success |
| 47 | mistral | devstral-latest | 18.0% |  | account_specific_free | нет данных | success |
| 48 | mistral | mistral-code-agent-latest | 18.0% |  | account_specific_free | нет данных | timeout |
| 49 | mistral | mistral-small-2603 | 18.0% |  | account_specific_free | нет данных | success |
| 50 | mistral | mistral-small-latest | 18.0% |  | account_specific_free | нет данных | success |
| 51 | mistral | mistral-vibe-cli-fast | 18.0% |  | account_specific_free | нет данных | success |
| 52 | mistral | magistral-small-latest | 18.0% |  | account_specific_free | нет данных | success |
| 53 | mistral | magistral-medium-2509 | 18.0% |  | account_specific_free | нет данных | success |
| 54 | mistral | magistral-medium-latest | 18.0% |  | account_specific_free | нет данных | success |
| 55 | mistral | voxtral-small-2507 | 18.0% |  | account_specific_free | нет данных | success |
| 56 | mistral | voxtral-small-latest | 18.0% |  | account_specific_free | нет данных | success |
| 57 | mistral | labs-leanstral-1-5-1 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 58 | mistral | labs-leanstral-1-5 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 59 | mistral | mistral-large-2512 | 18.0% |  | account_specific_free | нет данных | success |
| 60 | mistral | mistral-large-latest | 18.0% |  | account_specific_free | нет данных | success |
| 61 | mistral | ministral-3b-2512 | 18.0% |  | account_specific_free | нет данных | success |
| 62 | mistral | ministral-3b-latest | 18.0% |  | account_specific_free | нет данных | success |
| 63 | mistral | ministral-8b-2512 | 18.0% |  | account_specific_free | нет данных | success |
| 64 | mistral | ministral-8b-latest | 18.0% |  | account_specific_free | нет данных | success |
| 65 | mistral | ministral-14b-2512 | 18.0% |  | account_specific_free | нет данных | success |
| 66 | mistral | ministral-14b-latest | 18.0% |  | account_specific_free | нет данных | success |
| 67 | mistral | mistral-medium-latest | 18.0% |  | account_specific_free | нет данных | success |
| 68 | mistral | mistral-medium-3-5 | 18.0% |  | account_specific_free | нет данных | success |
| 69 | mistral | mistral-medium-3.5 | 18.0% |  | account_specific_free | нет данных | success |
| 70 | mistral | mistral-medium-2604 | 18.0% |  | account_specific_free | нет данных | success |
| 71 | mistral | mistral-vibe-cli-latest | 18.0% |  | account_specific_free | нет данных | success |
| 72 | mistral | mistral-vibe-cli-with-tools | 18.0% |  | account_specific_free | нет данных | success |
| 73 | mistral | magistral-small-2509 | 18.0% |  | account_specific_free | нет данных | success |
| 74 | mistral | mistral-small-2506 | 18.0% |  | account_specific_free | нет данных | success |
| 75 | mistral | mistral-embed-2312 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 76 | mistral | mistral-embed | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 77 | mistral | codestral-embed | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 78 | mistral | codestral-embed-2505 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 79 | mistral | mistral-moderation-2603 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 80 | mistral | mistral-ocr-2512 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 81 | mistral | mistral-ocr-3-0 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 82 | mistral | mistral-ocr-3 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 83 | mistral | mistral-ocr-latest | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 84 | mistral | mistral-ocr-4-0 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 85 | mistral | mistral-ocr-4 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 86 | mistral | voxtral-mini-2602 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 87 | mistral | voxtral-mini-latest | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 88 | mistral | voxtral-mini-transcribe-realtime-2602 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 89 | mistral | voxtral-mini-realtime-2602 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 90 | mistral | voxtral-mini-realtime-latest | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 91 | mistral | voxtral-mini-tts-2603 | 18.0% |  | account_specific_free | нет данных | invalid_response |
| 92 | mistral | voxtral-mini-tts-latest | 18.0% |  | account_specific_free | нет данных | invalid_response |

## Все ранжированные модели

| № | Модель | Качество (%) | Уверенность | Бесплатность | Штрафы | В маршруте |
|---:|---|---:|:---:|:---:|:---:|:---:|
| 1 | opencode_zen/gpt-5.5 | 90.9 | high | — | no_tool_calling: -5.0 | — |
| 2 | openrouter/moonshotai/kimi-k2.6 | 86.3 | high | — | — | — |
| 3 | openrouter/xiaomi/mimo-v2.5-pro | 84.6 | high | — | — | — |
| 4 | openrouter/nex-agi/nex-n2-pro | 83.4 | high | — | — | — |
| 5 | openrouter/xiaomi/mimo-v2.5 | 80.9 | high | — | — | — |
| 6 | opencode_zen/minimax-m3 | 73.3 | high | — | no_tool_calling: -5.0 | — |
| 7 | opencode_zen/mimo-v2.5-free | 71.3 | high | — | no_tool_calling: -5.0 | — |
| 8 | opencode_zen/minimax-m2.7 | 66.8 | high | — | no_tool_calling: -5.0 | — |
| 9 | openrouter/cohere/north-mini-code:free | 58.9 | high | — | — | ✓ |
| 10 | openrouter/google/gemini-2.5-pro | 55.6 | high | — | — | — |
| 11 | openrouter/google/gemini-2.5-pro-preview | 55.6 | high | — | — | — |
| 12 | openrouter/google/gemini-2.5-pro-preview-05-06 | 55.6 | high | — | — | — |
| 13 | openrouter/mistralai/devstral-2512 | 53.3 | high | — | — | — |
| 14 | openrouter/inception/mercury-2 | 53.2 | high | — | — | — |
| 15 | openrouter/mistralai/mistral-small-3.1-24b-instruct | 47.9 | high | — | — | — |
| 16 | openrouter/mistralai/mistral-medium-3.1 | 41.7 | high | — | — | — |
| 17 | mistral/mistral-medium | 41.7 | high | — | — | ✓ |
| 18 | mistral/mistral-medium-3 | 41.7 | high | — | — | ✓ |
| 19 | openrouter/mistralai/mistral-large-2512 | 41.3 | high | — | — | — |
| 20 | openrouter/mistralai/mistral-small-3.2-24b-instruct | 33.1 | high | — | — | — |
| 21 | openrouter/openai/gpt-3.5-turbo-0613 | 24.7 | high | — | context_below_minimum (4095 < 128000): -8.0 | — |
| 22 | openrouter/openai/gpt-3.5-turbo-instruct | 24.7 | high | — | context_below_minimum (4095 < 128000): -8.0 | — |
| 23 | openrouter/openai/gpt-3.5-turbo-16k | 24.7 | high | — | context_below_minimum (16385 < 128000): -8.0 | — |
| 24 | openrouter/openai/gpt-3.5-turbo | 24.7 | high | — | context_below_minimum (16385 < 128000): -8.0 | — |
| 25 | openrouter/openai/o3-deep-research | 20.1 | high | — | — | — |
| 26 | openrouter/openai/o3-pro | 20.1 | high | — | — | — |
| 27 | openrouter/openai/o3 | 20.1 | high | — | — | — |
| 28 | openrouter/openai/o3-mini-high | 20.1 | high | — | — | — |
| 29 | openrouter/openai/o3-mini | 20.1 | high | — | — | — |
| 30 | openrouter/inclusionai/ling-2.6-1t | 20.0 | high | — | — | — |
| 31 | openrouter/moonshotai/kimi-k2.7-code | 19.9 | high | — | — | — |
| 32 | openrouter/moonshotai/kimi-k2.5 | 19.9 | high | — | — | — |
| 33 | openrouter/moonshotai/kimi-k2-thinking | 19.9 | high | — | — | — |
| 34 | openrouter/moonshotai/kimi-k2-0905 | 19.9 | high | — | — | — |
| 35 | openrouter/moonshotai/kimi-k2 | 19.9 | high | — | — | — |
| 36 | openrouter/openai/gpt-4.1 | 19.9 | high | — | — | — |
| 37 | openrouter/openai/gpt-4.1-mini | 19.9 | high | — | — | — |
| 38 | openrouter/openai/gpt-4.1-nano | 19.9 | high | — | — | — |
| 39 | openrouter/qwen/qwen3-vl-30b-a3b-instruct | 19.8 | high | — | — | — |
| 40 | openrouter/qwen/qwen3-next-80b-a3b-instruct | 19.8 | high | — | — | — |
| 41 | openrouter/mistralai/mistral-medium-3-5 | 19.7 | high | — | — | — |
| 42 | openrouter/qwen/qwen3-vl-8b-instruct | 19.7 | high | — | — | — |
| 43 | openrouter/mistralai/mistral-medium-3 | 19.7 | high | — | — | — |
| 44 | openrouter/cohere/command-a | 19.7 | high | — | — | — |
| 45 | openrouter/amazon/nova-micro-v1 | 19.7 | high | — | — | — |
| 46 | openrouter/amazon/nova-pro-v1 | 19.7 | high | — | — | — |
| 47 | openrouter/anthropic/claude-3-haiku | 19.7 | high | — | — | — |
| 48 | openrouter/mistralai/mistral-large | 19.7 | high | — | — | — |
| 49 | openrouter/ibm-granite/granite-4.0-h-micro | 19.6 | high | — | — | — |
| 50 | openrouter/poolside/laguna-s-2.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 51 | openrouter/poolside/laguna-s-2.1:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 52 | openrouter/google/gemini-3.6-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 53 | openrouter/google/gemini-3.5-flash-lite | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 54 | openrouter/meituan/longcat-2.0 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 55 | openrouter/thinkingmachines/inkling | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 56 | openrouter/openrouter/auto-beta | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 57 | openrouter/moonshotai/kimi-k3 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 58 | openrouter/meta/muse-spark-1.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 59 | openrouter/kwaipilot/kat-coder-air-v2.5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 60 | openrouter/kwaipilot/kat-coder-pro-v2.5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 61 | openrouter/openai/gpt-5.6-luna-pro | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 62 | openrouter/openai/gpt-5.6-luna | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 63 | openrouter/openai/gpt-5.6-terra-pro | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 64 | openrouter/openai/gpt-5.6-terra | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 65 | openrouter/openai/gpt-5.6-sol-pro | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 66 | openrouter/openai/gpt-5.6-sol | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 67 | openrouter/x-ai/grok-4.5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 68 | openrouter/~x-ai/grok-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 69 | openrouter/aion-labs/aion-3.0-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 70 | openrouter/aion-labs/aion-3.0 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 71 | openrouter/tencent/hy3 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 72 | openrouter/poolside/laguna-xs-2.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 73 | openrouter/poolside/laguna-xs-2.1:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 74 | openrouter/anthropic/claude-sonnet-5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 75 | openrouter/google/gemini-3.1-flash-lite-image | 18.0 | low | — | context_below_minimum (65536 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 76 | openrouter/nex-agi/nex-n2-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 77 | openrouter/sakana/fugu-ultra | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 78 | openrouter/google/gemini-3.1-flash-image | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 79 | openrouter/google/gemini-3-pro-image | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 80 | openrouter/z-ai/glm-5.2 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 81 | openrouter/openrouter/fusion | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 82 | openrouter/~anthropic/claude-fable-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 83 | openrouter/anthropic/claude-fable-5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 84 | openrouter/nvidia/nemotron-3.5-content-safety:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 85 | openrouter/nvidia/nemotron-3-ultra-550b-a55b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 86 | openrouter/nvidia/nemotron-3-ultra-550b-a55b:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 87 | openrouter/qwen/qwen3.7-plus | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 88 | openrouter/minimax/minimax-m3 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 89 | openrouter/stepfun/step-3.7-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 90 | openrouter/anthropic/claude-opus-4.8-fast | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 91 | openrouter/anthropic/claude-opus-4.8 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 92 | openrouter/qwen/qwen3.7-max | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 93 | openrouter/x-ai/grok-build-0.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 94 | openrouter/google/gemini-3.5-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 95 | openrouter/anthropic/claude-opus-4.7-fast | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 96 | openrouter/perceptron/perceptron-mk1 | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 97 | openrouter/inclusionai/ring-2.6-1t | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 98 | openrouter/google/gemini-3.1-flash-lite | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 99 | openrouter/openai/gpt-chat-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 100 | openrouter/x-ai/grok-4.3 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 101 | openrouter/ibm-granite/granite-4.1-8b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 102 | openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 103 | openrouter/poolside/laguna-m.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 104 | openrouter/poolside/laguna-m.1:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 105 | openrouter/~anthropic/claude-haiku-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 106 | openrouter/~openai/gpt-mini-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 107 | openrouter/~google/gemini-pro-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 108 | openrouter/~moonshotai/kimi-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 109 | openrouter/~google/gemini-flash-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 110 | openrouter/~anthropic/claude-sonnet-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 111 | openrouter/~openai/gpt-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 112 | openrouter/qwen/qwen3.5-plus-20260420 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 113 | openrouter/qwen/qwen3.6-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 114 | openrouter/qwen/qwen3.6-35b-a3b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 115 | openrouter/qwen/qwen3.6-max-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 116 | openrouter/qwen/qwen3.6-27b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 117 | openrouter/openai/gpt-5.5-pro | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 118 | openrouter/openai/gpt-5.5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 119 | openrouter/deepseek/deepseek-v4-pro | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 120 | openrouter/deepseek/deepseek-v4-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 121 | openrouter/tencent/hy3-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 122 | openrouter/openai/gpt-5.4-image-2 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 123 | openrouter/inclusionai/ling-2.6-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 124 | openrouter/~anthropic/claude-opus-latest | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 125 | openrouter/openrouter/pareto-code | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 126 | openrouter/anthropic/claude-opus-4.7 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 127 | openrouter/z-ai/glm-5.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 128 | openrouter/google/gemma-4-26b-a4b-it | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 129 | openrouter/google/gemma-4-26b-a4b-it:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 130 | openrouter/google/gemma-4-31b-it | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 131 | openrouter/google/gemma-4-31b-it:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 132 | openrouter/qwen/qwen3.6-plus | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 133 | openrouter/z-ai/glm-5v-turbo | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 134 | openrouter/arcee-ai/trinity-large-thinking | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 135 | openrouter/x-ai/grok-4.20-multi-agent | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 136 | openrouter/x-ai/grok-4.20 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 137 | openrouter/google/lyria-3-pro-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 138 | openrouter/google/lyria-3-clip-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 139 | openrouter/kwaipilot/kat-coder-pro-v2 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 140 | openrouter/rekaai/reka-edge | 18.0 | low | — | context_below_minimum (16384 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 141 | openrouter/minimax/minimax-m2.7 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 142 | openrouter/openai/gpt-5.4-nano | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 143 | openrouter/openai/gpt-5.4-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 144 | openrouter/mistralai/mistral-small-2603 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 145 | openrouter/z-ai/glm-5-turbo | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 146 | openrouter/nvidia/nemotron-3-super-120b-a12b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 147 | openrouter/nvidia/nemotron-3-super-120b-a12b:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 148 | openrouter/bytedance-seed/seed-2.0-lite | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 149 | openrouter/qwen/qwen3.5-9b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 150 | openrouter/openai/gpt-5.4-pro | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 151 | openrouter/openai/gpt-5.4 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 152 | openrouter/openai/gpt-5.3-chat | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 153 | openrouter/google/gemini-3.1-flash-lite-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 154 | openrouter/bytedance-seed/seed-2.0-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 155 | openrouter/google/gemini-3.1-flash-image-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 156 | openrouter/qwen/qwen3.5-35b-a3b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 157 | openrouter/qwen/qwen3.5-27b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 158 | openrouter/qwen/qwen3.5-122b-a10b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 159 | openrouter/qwen/qwen3.5-flash-02-23 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 160 | openrouter/google/gemini-3.1-pro-preview-customtools | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 161 | openrouter/openai/gpt-5.3-codex | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 162 | openrouter/aion-labs/aion-2.0 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 163 | openrouter/google/gemini-3.1-pro-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 164 | openrouter/anthropic/claude-sonnet-4.6 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 165 | openrouter/qwen/qwen3.5-plus-02-15 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 166 | openrouter/qwen/qwen3.5-397b-a17b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 167 | openrouter/minimax/minimax-m2.5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 168 | openrouter/z-ai/glm-5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 169 | openrouter/qwen/qwen3-max-thinking | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 170 | openrouter/anthropic/claude-opus-4.6 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 171 | openrouter/qwen/qwen3-coder-next | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 172 | openrouter/openrouter/free | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 173 | openrouter/stepfun/step-3.5-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 174 | openrouter/upstage/solar-pro-3 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 175 | openrouter/minimax/minimax-m2-her | 18.0 | low | — | context_below_minimum (65536 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 176 | openrouter/writer/palmyra-x5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 177 | openrouter/openai/gpt-audio | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 178 | openrouter/openai/gpt-audio-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 179 | openrouter/z-ai/glm-4.7-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 180 | openrouter/openai/gpt-5.2-codex | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 181 | openrouter/bytedance-seed/seed-1.6-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 182 | openrouter/bytedance-seed/seed-1.6 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 183 | openrouter/minimax/minimax-m2.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 184 | openrouter/z-ai/glm-4.7 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 185 | openrouter/google/gemini-3-flash-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 186 | openrouter/nvidia/nemotron-3-nano-30b-a3b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 187 | openrouter/nvidia/nemotron-3-nano-30b-a3b:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 188 | openrouter/openai/gpt-5.2-chat | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 189 | openrouter/openai/gpt-5.2-pro | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 190 | openrouter/openai/gpt-5.2 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 191 | openrouter/relace/relace-search | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 192 | openrouter/z-ai/glm-4.6v | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 193 | openrouter/openrouter/bodybuilder | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 194 | openrouter/openai/gpt-5.1-codex-max | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 195 | openrouter/amazon/nova-2-lite-v1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 196 | openrouter/mistralai/ministral-14b-2512 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 197 | openrouter/mistralai/ministral-8b-2512 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 198 | openrouter/mistralai/ministral-3b-2512 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 199 | openrouter/deepseek/deepseek-v3.2 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 200 | openrouter/anthropic/claude-opus-4.5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 201 | openrouter/allenai/olmo-3-32b-think | 18.0 | low | — | context_below_minimum (65536 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 202 | openrouter/google/gemini-3-pro-image-preview | 18.0 | low | — | context_below_minimum (65536 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 203 | openrouter/deepcogito/cogito-v2.1-671b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 204 | openrouter/openai/gpt-5.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 205 | openrouter/openai/gpt-5.1-chat | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 206 | openrouter/openai/gpt-5.1-codex | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 207 | openrouter/openai/gpt-5.1-codex-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 208 | openrouter/amazon/nova-premier-v1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 209 | openrouter/perplexity/sonar-pro-search | 18.0 | high | — | — | — |
| 210 | openrouter/mistralai/voxtral-small-24b-2507 | 18.0 | low | — | context_below_minimum (32000 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 211 | openrouter/openai/gpt-oss-safeguard-20b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 212 | openrouter/nvidia/nemotron-nano-12b-v2-vl:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 213 | openrouter/minimax/minimax-m2 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 214 | openrouter/qwen/qwen3-vl-32b-instruct | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 215 | openrouter/openai/gpt-5-image-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 216 | openrouter/anthropic/claude-haiku-4.5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 217 | openrouter/qwen/qwen3-vl-8b-thinking | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 218 | openrouter/openai/gpt-5-image | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 219 | openrouter/openai/o4-mini-deep-research | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 220 | openrouter/google/gemini-2.5-flash-image | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 221 | openrouter/qwen/qwen3-vl-30b-a3b-thinking | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 222 | openrouter/openai/gpt-5-pro | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 223 | openrouter/z-ai/glm-4.6 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 224 | openrouter/anthropic/claude-sonnet-4.5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 225 | openrouter/deepseek/deepseek-v3.2-exp | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 226 | openrouter/thedrummer/cydonia-24b-v4.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 227 | openrouter/relace/relace-apply-3 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 228 | openrouter/qwen/qwen3-vl-235b-a22b-thinking | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 229 | openrouter/qwen/qwen3-vl-235b-a22b-instruct | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 230 | openrouter/qwen/qwen3-max | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 231 | openrouter/qwen/qwen3-coder-plus | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 232 | openrouter/openai/gpt-5-codex | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 233 | openrouter/deepseek/deepseek-v3.1-terminus | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 234 | openrouter/qwen/qwen3-coder-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 235 | openrouter/qwen/qwen3-next-80b-a3b-thinking | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 236 | openrouter/qwen/qwen-plus-2025-07-28 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 237 | openrouter/qwen/qwen-plus-2025-07-28:thinking | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 238 | openrouter/nvidia/nemotron-nano-9b-v2:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 239 | openrouter/qwen/qwen3-30b-a3b-thinking-2507 | 18.0 | low | — | context_below_minimum (81920 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 240 | openrouter/nousresearch/hermes-4-70b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 241 | openrouter/nousresearch/hermes-4-405b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 242 | openrouter/deepseek/deepseek-chat-v3.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 243 | openrouter/z-ai/glm-4.5v | 18.0 | low | — | context_below_minimum (65536 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 244 | openrouter/ai21/jamba-large-1.7 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 245 | openrouter/openai/gpt-5-chat | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 246 | openrouter/openai/gpt-5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 247 | openrouter/openai/gpt-5-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 248 | openrouter/openai/gpt-5-nano | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 249 | openrouter/openai/gpt-oss-120b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 250 | openrouter/openai/gpt-oss-20b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 251 | openrouter/openai/gpt-oss-20b:free | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 252 | openrouter/anthropic/claude-opus-4.1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 253 | openrouter/mistralai/codestral-2508 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 254 | openrouter/qwen/qwen3-coder-30b-a3b-instruct | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 255 | openrouter/qwen/qwen3-30b-a3b-instruct-2507 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 256 | openrouter/z-ai/glm-4.5 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 257 | openrouter/z-ai/glm-4.5-air | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 258 | openrouter/qwen/qwen3-235b-a22b-thinking-2507 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 259 | openrouter/qwen/qwen3-coder | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 260 | openrouter/bytedance/ui-tars-1.5-7b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 261 | openrouter/google/gemini-2.5-flash-lite | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 262 | openrouter/qwen/qwen3-235b-a22b-2507 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 263 | openrouter/cognitivecomputations/dolphin-mistral-24b-venice-edition | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 264 | openrouter/tencent/hunyuan-a13b-instruct | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 265 | openrouter/morph/morph-v3-large | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 266 | openrouter/morph/morph-v3-fast | 18.0 | low | — | context_below_minimum (81920 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 267 | openrouter/baidu/ernie-4.5-vl-424b-a47b | 18.0 | low | — | context_below_minimum (123000 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 268 | openrouter/minimax/minimax-m1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 269 | openrouter/google/gemini-2.5-flash | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 270 | openrouter/deepseek/deepseek-r1-0528 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 271 | openrouter/anthropic/claude-opus-4 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 272 | openrouter/anthropic/claude-sonnet-4 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 273 | openrouter/google/gemma-3n-e4b-it | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 274 | openrouter/arcee-ai/virtuoso-large | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 275 | openrouter/meta-llama/llama-guard-4-12b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 276 | openrouter/qwen/qwen3-30b-a3b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 277 | openrouter/qwen/qwen3-8b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 278 | openrouter/qwen/qwen3-14b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 279 | openrouter/qwen/qwen3-32b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 280 | openrouter/qwen/qwen3-235b-a22b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 281 | openrouter/openai/o4-mini-high | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 282 | openrouter/openai/o4-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 283 | openrouter/meta-llama/llama-4-maverick | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 284 | openrouter/meta-llama/llama-4-scout | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 285 | openrouter/deepseek/deepseek-chat-v3-0324 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 286 | openrouter/openai/o1-pro | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 287 | openrouter/google/gemma-3-4b-it | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 288 | openrouter/google/gemma-3-12b-it | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 289 | openrouter/openai/gpt-4o-mini-search-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 290 | openrouter/openai/gpt-4o-search-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 291 | openrouter/rekaai/reka-flash-3 | 18.0 | low | — | context_below_minimum (65536 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 292 | openrouter/google/gemma-3-27b-it | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 293 | openrouter/thedrummer/skyfall-36b-v2 | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 294 | openrouter/perplexity/sonar-reasoning-pro | 18.0 | high | — | — | — |
| 295 | openrouter/perplexity/sonar-pro | 18.0 | high | — | — | — |
| 296 | openrouter/perplexity/sonar-deep-research | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 297 | openrouter/mistralai/mistral-saba | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 298 | openrouter/aion-labs/aion-rp-llama-3.1-8b | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 299 | openrouter/qwen/qwen2.5-vl-72b-instruct | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 300 | openrouter/qwen/qwen-plus | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 301 | openrouter/mistralai/mistral-small-24b-instruct-2501 | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 302 | openrouter/perplexity/sonar | 18.0 | low | — | context_below_minimum (127072 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 303 | openrouter/deepseek/deepseek-r1-distill-llama-70b | 18.0 | low | — | context_below_minimum (8192 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 304 | openrouter/deepseek/deepseek-r1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 305 | openrouter/minimax/minimax-01 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 306 | openrouter/microsoft/phi-4 | 18.0 | low | — | context_below_minimum (16384 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 307 | openrouter/deepseek/deepseek-chat | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 308 | openrouter/sao10k/l3.3-euryale-70b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 309 | openrouter/openai/o1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 310 | openrouter/cohere/command-r7b-12-2024 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 311 | openrouter/meta-llama/llama-3.3-70b-instruct | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 312 | openrouter/amazon/nova-lite-v1 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 313 | openrouter/openai/gpt-4o-2024-11-20 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 314 | openrouter/mistralai/mistral-large-2407 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 315 | openrouter/qwen/qwen-2.5-coder-32b-instruct | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 316 | openrouter/thedrummer/unslopnemo-12b | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 317 | openrouter/anthracite-org/magnum-v4-72b | 18.0 | low | — | context_below_minimum (16384 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 318 | openrouter/qwen/qwen-2.5-7b-instruct | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 319 | openrouter/inflection/inflection-3-pi | 18.0 | low | — | context_below_minimum (8000 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 320 | openrouter/inflection/inflection-3-productivity | 18.0 | low | — | context_below_minimum (8000 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 321 | openrouter/thedrummer/rocinante-12b | 18.0 | low | — | context_below_minimum (65536 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 322 | openrouter/meta-llama/llama-3.2-1b-instruct | 18.0 | low | — | context_below_minimum (60000 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 323 | openrouter/meta-llama/llama-3.2-3b-instruct | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 324 | openrouter/qwen/qwen-2.5-72b-instruct | 18.0 | low | — | context_below_minimum (32768 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 325 | openrouter/cohere/command-r-08-2024 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 326 | openrouter/cohere/command-r-plus-08-2024 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 327 | openrouter/sao10k/l3.1-euryale-70b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 328 | openrouter/nousresearch/hermes-3-llama-3.1-70b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 329 | openrouter/nousresearch/hermes-3-llama-3.1-405b | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 330 | openrouter/sao10k/l3-lunaris-8b | 18.0 | low | — | context_below_minimum (8192 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 331 | openrouter/openai/gpt-4o-2024-08-06 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 332 | openrouter/meta-llama/llama-3.1-70b-instruct | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 333 | openrouter/meta-llama/llama-3.1-8b-instruct | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 334 | openrouter/mistralai/mistral-nemo | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 335 | openrouter/openai/gpt-4o-mini | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 336 | openrouter/openai/gpt-4o-mini-2024-07-18 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 337 | openrouter/google/gemma-2-27b-it | 18.0 | low | — | context_below_minimum (8192 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 338 | openrouter/openai/gpt-4o | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 339 | openrouter/openai/gpt-4o-2024-05-13 | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 340 | openrouter/mistralai/mixtral-8x22b-instruct | 18.0 | low | — | context_below_minimum (65536 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 341 | openrouter/microsoft/wizardlm-2-8x22b | 18.0 | low | — | context_below_minimum (65535 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 342 | openrouter/openai/gpt-4-turbo | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 343 | openrouter/openai/gpt-4-turbo-preview | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 344 | openrouter/openrouter/auto | 18.0 | low | — | low_match_confidence: -4.0 | — |
| 345 | openrouter/mancer/weaver | 18.0 | low | — | context_below_minimum (8000 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 346 | openrouter/undi95/remm-slerp-l2-13b | 18.0 | low | — | context_below_minimum (6144 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 347 | openrouter/gryphe/mythomax-l2-13b | 18.0 | low | — | context_below_minimum (8192 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 348 | openrouter/openai/gpt-4 | 18.0 | low | — | context_below_minimum (8191 < 128000): -8.0, low_match_confidence: -4.0 | — |
| 349 | opencode_zen/claude-fable-5 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 350 | opencode_zen/claude-opus-4-8 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 351 | opencode_zen/claude-opus-4-7 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 352 | opencode_zen/claude-opus-4-6 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 353 | opencode_zen/claude-opus-4-5 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 354 | opencode_zen/claude-opus-4-1 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 355 | opencode_zen/claude-sonnet-5 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 356 | opencode_zen/claude-sonnet-4-6 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 357 | opencode_zen/claude-sonnet-4-5 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 358 | opencode_zen/claude-sonnet-4 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 359 | opencode_zen/claude-haiku-4-5 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 360 | opencode_zen/gemini-3.6-flash | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 361 | opencode_zen/gemini-3.5-flash-lite | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 362 | opencode_zen/gemini-3.5-flash | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 363 | opencode_zen/gemini-3.1-pro | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 364 | opencode_zen/gemini-3-flash | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 365 | opencode_zen/gpt-5.6-sol | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 366 | opencode_zen/gpt-5.6-terra | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 367 | opencode_zen/gpt-5.6-luna | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 368 | opencode_zen/gpt-5.5-pro | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 369 | opencode_zen/gpt-5.4 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 370 | opencode_zen/gpt-5.4-pro | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 371 | opencode_zen/gpt-5.4-mini | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 372 | opencode_zen/gpt-5.4-nano | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 373 | opencode_zen/gpt-5.3-codex-spark | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 374 | opencode_zen/gpt-5.3-codex | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 375 | opencode_zen/gpt-5.2 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 376 | opencode_zen/gpt-5.2-codex | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 377 | opencode_zen/gpt-5.1 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 378 | opencode_zen/gpt-5.1-codex-max | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 379 | opencode_zen/gpt-5.1-codex | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 380 | opencode_zen/gpt-5.1-codex-mini | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 381 | opencode_zen/gpt-5 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 382 | opencode_zen/gpt-5-codex | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 383 | opencode_zen/gpt-5-nano | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 384 | opencode_zen/grok-build-0.1 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 385 | opencode_zen/grok-4.5 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 386 | opencode_zen/deepseek-v4-pro | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 387 | opencode_zen/deepseek-v4-flash | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 388 | opencode_zen/glm-5.2 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 389 | opencode_zen/glm-5.1 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 390 | opencode_zen/glm-5 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 391 | opencode_zen/minimax-m2.5 | 18.0 | high | — | no_tool_calling: -5.0 | — |
| 392 | opencode_zen/kimi-k2.7-code | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 393 | opencode_zen/kimi-k2.6 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 394 | opencode_zen/kimi-k2.5 | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 395 | opencode_zen/qwen3.6-plus | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 396 | opencode_zen/qwen3.5-plus | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 397 | opencode_zen/big-pickle | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 398 | opencode_zen/deepseek-v4-flash-free | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 399 | opencode_zen/nemotron-3-ultra-free | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 400 | opencode_zen/north-mini-code-free | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 401 | opencode_zen/laguna-s-2.1-free | 18.0 | low | — | no_tool_calling: -5.0, low_match_confidence: -4.0 | — |
| 402 | zai/glm-4.5 | 18.0 | high | — | — | ✓ |
| 403 | zai/glm-4.5-air | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 404 | zai/glm-4.6 | 18.0 | high | — | — | ✓ |
| 405 | zai/glm-4.7 | 18.0 | high | — | — | ✓ |
| 406 | zai/glm-5 | 18.0 | high | — | — | ✓ |
| 407 | zai/glm-5-turbo | 18.0 | high | — | — | ✓ |
| 408 | zai/glm-5.1 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 409 | zai/glm-5.2 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 410 | groq/canopylabs/orpheus-v1-english | 18.0 | low | — | context_below_minimum (4000 < 128000): -8.0, low_match_confidence: -4.0 | ✓ |
| 411 | groq/groq/compound-mini | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 412 | groq/llama-3.3-70b-versatile | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 413 | groq/groq/compound | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 414 | groq/qwen/qwen3.6-27b | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 415 | groq/llama-3.1-8b-instant | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 416 | groq/openai/gpt-oss-20b | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 417 | groq/canopylabs/orpheus-arabic-saudi | 18.0 | low | — | context_below_minimum (4000 < 128000): -8.0, low_match_confidence: -4.0 | ✓ |
| 418 | groq/openai/gpt-oss-120b | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 419 | groq/allam-2-7b | 18.0 | low | — | context_below_minimum (4096 < 128000): -8.0, low_match_confidence: -4.0 | ✓ |
| 420 | mistral/mistral-medium-2505 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 421 | mistral/mistral-medium-2508 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 422 | mistral/open-mistral-nemo | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 423 | mistral/open-mistral-nemo-2407 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 424 | mistral/mistral-tiny-2407 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 425 | mistral/mistral-tiny-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 426 | mistral/codestral-2508 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 427 | mistral/codestral-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 428 | mistral/mistral-code-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 429 | mistral/mistral-code-fim-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 430 | mistral/devstral-2512 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 431 | mistral/devstral-medium-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 432 | mistral/devstral-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 433 | mistral/mistral-code-agent-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 434 | mistral/mistral-small-2603 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 435 | mistral/mistral-small-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 436 | mistral/mistral-vibe-cli-fast | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 437 | mistral/magistral-small-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 438 | mistral/magistral-medium-2509 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 439 | mistral/magistral-medium-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 440 | mistral/voxtral-small-2507 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 441 | mistral/voxtral-small-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 442 | mistral/labs-leanstral-1-5-1 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 443 | mistral/labs-leanstral-1-5 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 444 | mistral/mistral-large-2512 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 445 | mistral/mistral-large-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 446 | mistral/ministral-3b-2512 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 447 | mistral/ministral-3b-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 448 | mistral/ministral-8b-2512 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 449 | mistral/ministral-8b-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 450 | mistral/ministral-14b-2512 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 451 | mistral/ministral-14b-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 452 | mistral/mistral-medium-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 453 | mistral/mistral-medium-3-5 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 454 | mistral/mistral-medium-3.5 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 455 | mistral/mistral-medium-2604 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 456 | mistral/mistral-vibe-cli-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 457 | mistral/mistral-vibe-cli-with-tools | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 458 | mistral/magistral-small-2509 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 459 | mistral/mistral-small-2506 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 460 | mistral/mistral-embed-2312 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 461 | mistral/mistral-embed | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 462 | mistral/codestral-embed | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 463 | mistral/codestral-embed-2505 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 464 | mistral/mistral-moderation-2603 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 465 | mistral/mistral-ocr-2512 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 466 | mistral/mistral-ocr-3-0 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 467 | mistral/mistral-ocr-3 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 468 | mistral/mistral-ocr-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 469 | mistral/mistral-ocr-4-0 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 470 | mistral/mistral-ocr-4 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 471 | mistral/voxtral-mini-2602 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 472 | mistral/voxtral-mini-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 473 | mistral/voxtral-mini-transcribe-realtime-2602 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 474 | mistral/voxtral-mini-realtime-2602 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 475 | mistral/voxtral-mini-realtime-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 476 | mistral/voxtral-mini-tts-2603 | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |
| 477 | mistral/voxtral-mini-tts-latest | 18.0 | low | — | low_match_confidence: -4.0 | ✓ |

### Легенда

- **Качество (%)**: итоговая оценка относительно ChatGPT-5.6 Sol High = 100%
- **Уверенность**: high (есть прямой Coding Agent Index), medium (косвенные данные), low (нет данных)
- **Штрафы**: применённые штрафы с указанием величины
- **В маршруте**: модель включена в сгенерированный LiteLLM config

---
*AI-тестирование проведено через Artificial Analysis Coding Agent Index и дополнительные источники.*