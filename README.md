# maraim 1.0 — Sprint 1 Real Foundation

هذه نسخة أساس حقيقية صغيرة وليست المنتج النهائي.

## الموجود فعليًا
- Python stdlib فقط، بدون npm وبدون pip install.
- SQLite حقيقية في `data/maraim.sqlite`.
- Kernel بسيط: Event logging + runtime objects.
- DNA Source of Truth + Overrides.
- DNA Compiler يحول ملفات JSON/MD/TXT إلى Runtime Objects داخل DB.
- MCP Tools داخلية.
- Scraping Sources + Project Inbox.
- Chat Controller واحد يوجه داخليًا.
- Ollama Router اختياري مع fallback.

## التشغيل على Windows
افتح:
`start_maraim_windows.bat`

ثم:
`http://127.0.0.1:8790`

## اختبار سريع
- `/api/status`
- من الواجهة: Compile DNA / Run Sample Scraping / Ask
