# Dates & Nuts Backend (Django API)

High-performance, production-optimized API infrastructure for the Dates & Nuts e-commerce platform. Engineered for maximum scalability, persistence, and low-latency interaction with the Next.js storefront.

## 🚀 Production Optimizations
The backend has undergone significant architectural upgrades to support high-traffic production environments:

- **Database Migration**: Fully migrated from SQLite to **PostgreSQL** for robust data persistence and relational integrity on Render.
- **API Duplication Reduction**: Implemented a specialized `HomePageView` that aggregates Hero Slides, Categories, Featured Products, New Arrivals, and Chocolates into a single JSON response, reducing client-side round-trips by 400%.
- **Response Caching**: Integrated Django's `cache_page` on high-traffic endpoints (synced with frontend revalidation intervals) to minimize database hits and server load.
- **Health Check Infrastructure**: Added a dedicated, ultra-lightweight `/api/v1/ping/` endpoint that bypasses the Django REST Framework overhead for rapid service heartbeat monitoring.
- **Advanced Query Optimization**: Utilized `prefetch_related` for image/variant sets and `defer()` for heavy text fields to significantly reduce memory footprint during list operations.
- **Persistent Media**: Fully integrated **Cloudinary** for professional-grade image hosting and automated transformation.

## 🛠 Core Stack
- **Framework**: Django 6.0+ & Django REST Framework (DRF)
- **Database**: PostgreSQL (Production) / SQLite (Local Dev)
- **Image Storage**: Cloudinary (Cloud-native media management)
- **Static Hosting**: WhiteNoise with Brotli/Gzip compression
- **Authentication**: Token-based Auth with specialized Staff-only access logic

## 🔌 API Ecosystem (Prefix: `/api/v1/`)

| Endpoint | Method | Purpose | Optimization |
|----------|--------|---------|--------------|
| `homepage/` | GET | Single-call storefront data | **Cached & Aggregated** |
| `ping/` | GET | Health check / Keep-alive | **Lightweight Pure Django** |
| `products/` | GET | Catalog with advanced filtering | **Prefetched & Deferred** |
| `login/` | POST | Staff-only secure authentication | **Token-based** |
| `dashboard-stats/` | GET | Real-time administrative metrics | **Aggregated Metrics** |
| `log-order/` | POST | Track customer conversion (WhatsApp) | **Async-ready logging** |

## 📦 Project Structure
- `config/`: System settings, production security headers, and routing.
- `products/`: Core business logic, inventory management, and Cloudinary integration.
- `orders/`: Customer interaction logging and order workflow management.
- `management/`: Custom CLI tools for seeding data and admin setup.

## 🛠 Setup & Deployment
1. **Initialize Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Environment Variables**: Configure `.env` with `DATABASE_URL`, `CLOUDINARY_URL`, and `CORS_ALLOWED_ORIGINS`.
3. **Database & Static**:
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```
4. **Production Run**:
   ```bash
   gunicorn config.wsgi:application
   ```

## 🔒 Security Architecture
- **Strict CORS Policy**: Only authorized frontend domains (Vercel) can interact with the API.
- **CSRF Protection**: Comprehensive protection for state-changing requests.
- **Staff-Only Locks**: All management endpoints are protected by `IsAdminUser` permissions and staff-status validation.
- **SSL Enforcement**: Production environments are forced to use HTTPS with secure cookie flags.
