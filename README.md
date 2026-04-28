# Dates & Nuts Backend (Django API)

Essential backend infrastructure for the Dates & Nuts platform. Handles data persistence, admin authentication, and storefront API integration.

## 🛠 Core Stack
- Django 6.0+ & DRF
- Token Authentication
- PostgreSQL (Primary) / SQLite (Fallback)

## 🚀 Quick Setup
1. **Virtual Env**: `python -m venv venv` -> `.\venv\Scripts\activate` (Windows)
2. **Install**: `pip install django djangorestframework django-cors-headers django-filter psycopg2-binary python-dotenv`
3. **Environment**: Create `.env` with:
   - `DEBUG=True`, `SECRET_KEY`, `ALLOWED_HOSTS`
   - `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
4. **Initialize**: `python manage.py migrate` -> `python manage.py createsuperuser`
5. **Start**: `python manage.py runserver`

## 🔌 API Reference (Base: `/api/v1/`)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `login/` | POST | None | Staff-only login (Returns Token) |
| `products/` | GET | None | Fetch storefront products |
| `products/` | POST/PATCH | Token | Manage inventory (Admin) |
| `categories/` | GET | None | Fetch storefront categories |
| `heroslides/` | GET | None | Fetch dynamic carousel slides |
| `dashboard-stats/` | GET | Token | Admin dashboard metrics |
| `log-order/` | POST | None | Record WhatsApp click activity |

## 🔒 Security Logic
- **Admin Access**: Only users with `is_staff=True` or `is_superuser=True` can authenticate.
- **Auth Interceptor**: All management requests must include `Authorization: Token <key>`.
- **CORS**: Strictly restricted to defined frontend origins in `.env`.
