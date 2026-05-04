# Dates & Nuts Backend (Django API)

High-performance API infrastructure for the Dates & Nuts platform. Designed for scalability, security, and seamless integration with the Next.js storefront.

## 🛠 Core Stack
- **Framework**: Django 6.0+ & Django REST Framework (DRF)
- **Database**: PostgreSQL (Primary) with SQLite support for local development
- **Authentication**: DRF Token-based Auth system
- **Middleware**: Custom CORS management and CSRF protection for cross-origin storefront requests

## 🚀 Quick Setup
1. **Virtual Environment**: 
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```
2. **Install Requirements**:
   ```bash
   pip install django djangorestframework django-cors-headers django-filter psycopg2-binary python-dotenv
   ```
3. **Environment Configuration**: Create `.env`:
   ```env
   DEBUG=True
   SECRET_KEY=your_secret_key
   ALLOWED_HOSTS=127.0.0.1,localhost
   CORS_ALLOWED_ORIGINS=http://localhost:3000
   ```
4. **Database Migration**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```
5. **Run Server**:
   ```bash
   python manage.py runserver
   ```

## 🔌 API Ecosystem (Prefix: `/api/v1/`)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `login/` | POST | None | Staff-only login (Returns Token) |
| `products/` | GET | None | Fetch storefront catalog |
| `products/` | POST/PATCH | Token | Inventory management (Admin) |
| `categories/` | GET | None | Fetch storefront categories |
| `heroslides/` | GET | None | Fetch dynamic storefront carousel |
| `dashboard-stats/` | GET | Token | Real-time Admin metrics |
| `log-order/` | POST | None | Record customer WhatsApp activity |

## 🏗 Data Model Enhancements
- **Multi-Badge Support**: Products now support a dynamic `tags` array for the premium multi-tagging system.
- **Precision Pricing**: Implementation of base pricing and per-unit/kg logic for inventory consistency.
- **Activity Tracking**: Integrated `OrderLog` model to monitor conversion activity from WhatsApp redirects.

## 🔒 Security Architecture
- **Staff-Only Auth**: Authentication is strictly limited to users with `is_staff=True` to prevent unauthorized dashboard access.
- **CORS Strategy**: Production-ready CORS configuration strictly mapping permitted origins (e.g., Vercel frontend) to the Render API.
- **Environment Parity**: Standardized environment variable schema for seamless transitions between Local, Development, and Production environments.

## 🌍 Production Deployment
- **Backend (Render)**: Configured for Gunicorn with automated migrations and dynamic port binding.
- **Frontend (Vercel)**: Integrated with the backend API via secure environment variables.
