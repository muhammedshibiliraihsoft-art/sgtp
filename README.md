# Django Docker PostgreSQL DRF Project Starter

A production-ready Django REST Framework project template with Docker, PostgreSQL, and VS Code Dev Container support.

## SGTP repository status

This repository is being used for SGTP. Phase 1–2 foundations and the Phase 3 Supplier/Shop and User-Shop membership tasks exist. `Tenant` is the technical Shop representation, and a singleton `Supplier` plus `TenantMember`/`ShopRolePolicy` are present. T3-02 remediation is COMPLETE and fully closed. URL-path Shop context and complete cross-Shop isolation are not yet implemented; client, tailoring, billing, reports, and frontend business modules are also pending. The generic starter feature descriptions below do not mean SGTP V1 is complete or production-ready.

## ✨ Features

- 🐍 **Django 5.1** with Django REST Framework
- 🐘 **PostgreSQL** database with Docker
- 🐳 **Docker** development and production setup
- 🔧 **VS Code Dev Container** for consistent development environment
- 👥 **Custom User Model** with email authentication
- 🏢 **Supplier / Shop and User-Shop membership** foundation (request context and complete isolation pending T3-03)
- 🔐 **JWT Authentication** with DRF SimpleJWT
- 🌐 **CORS** configured for frontend integration
- 📊 **API Documentation** with drf-spectacular (Swagger/OpenAPI)
- 🗑️ **Soft Delete** with django-safedelete
- 🎯 **Base Models** and ViewSets for rapid development
- 🚀 **Production-ready** Dockerfile with Gunicorn
- 📦 **Auto-deployment** ready with migrations

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd django-docker-postgress-drf-project-starter-with-vscode-devcontainer-and-deployment-config
cp .env.example .env
```

### 2. Open in VS Code Dev Container
1. Open this folder in VS Code
2. When prompted, click "Reopen in Container" 
3. Or use Command Palette: `Dev Containers: Reopen in Container`
4. The devcontainer will automatically:
   - Wait for PostgreSQL to be ready
   - Install Python dependencies
   - Apply existing migrations

### 3. Create Superuser and Start Development
```bash
# Create superuser
make superuser

# Start development server
make dev
```

### 4. Access Your Application
- **Development Server**: http://localhost:8001
- **Admin Panel**: http://localhost:8001/admin
- **Browsable API**: http://localhost:8001/api/browse/ (sign in through Django Admin as Main Supplier; enter an access JWT to call API endpoints)
- **OpenAPI/Swagger docs**: http://localhost:8001/api/docs/ (same Main Supplier sign-in)
- **Root URL**: redirects to the protected Browsable API portal

## 📁 Project Structure

```
├── .devcontainer/          # VS Code Dev Container configuration
│   ├── devcontainer.json   # Dev container settings
│   ├── docker-compose.yml  # Development database setup
│   ├── wait-for-postgres.sh # Database readiness script
│   └── setup.sh            # Automated environment setup
├── .vscode/               # VS Code launch configurations
├── core/                  # Django project settings
├── apps/
│   ├── accounts/          # Custom user authentication
│   │   └── migrations/    # Database migrations (committed)
│   ├── tenants/           # Multi-tenant support
│   │   └── migrations/    # Database migrations (committed)
│   └── common/            # Shared models and utilities
├── templates/             # HTML templates
├── Dockerfile             # Production Docker image
├── Dockerfile.dev         # Development Docker image
├── docker-compose.prod.yml # Production compose
├── entrypoint.prod.sh     # Production startup script
├── Makefile              # Development commands and shortcuts
└── requirements.txt       # Python dependencies
```

## 🔧 Development

### Available Make Commands
```bash
make help              # Show all available commands
make dev               # Start development server
make makemigrations    # Create new migrations (when models change)
make migrate           # Apply existing migrations
make shell             # Open Django shell
make test              # Run tests
make superuser         # Create superuser
make lint              # Run code linting
make format            # Format code with black and isort
```

### Migration Workflow
**Important**: Migration files are committed to the repository. Only create new migrations when you modify models.

```bash
# When you modify models (manual step):
make makemigrations

# To apply existing migrations (automated in devcontainer):
make migrate

# Check migration status:
python manage.py showmigrations
```

### Database Management
```bash
# Reset database (development only)
python manage.py flush

# Create and apply migrations
make makemigrations
make migrate
```

## � DevContainer Features

### Automatic Setup
The devcontainer includes robust setup that:
- ✅ **Waits for PostgreSQL** to be ready before running Django commands
- ✅ **Installs dependencies** automatically
- ✅ **Applies migrations** from committed migration files
- ✅ **Handles timing issues** with database connectivity

### Setup Scripts
- **`wait-for-postgres.sh`**: Ensures database is ready before running commands
- **`setup.sh`**: Handles dependency installation and migrations
- **Clean workflow**: No migration generation in containers - only applies existing migrations

### VS Code Integration
- Pre-configured extensions for Python development
- Django-specific settings and formatters
- Integrated debugging support

## �🚀 Production Deployment

### Docker Commands
```bash
# Development
make build-dev         # Build development image

# Production
make build-prod        # Build production image
make prod-up           # Start production environment
make prod-down         # Stop production environment
make prod-logs         # View production logs
make clean             # Clean up Docker resources
```

### Manual Docker Build
```bash
# Production image
docker build -t your-app:latest -f Dockerfile .

# Development image
docker build -t your-app-dev:latest -f Dockerfile.dev .
```

### Environment Variables Required
```bash
# Database
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
DB_HOST=your_db_host
DB_PORT=5432

# Django
DJANGO_SECRET_KEY=your_very_secure_secret_key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

```

### Production Features
- ✅ **Auto-migrations** on container startup
- ✅ **Static file collection** with WhiteNoise
- ✅ **Health checks** and proper logging
- ✅ **Non-root user** for security
- ✅ **Optimized** multi-stage build

## 🔐 Authentication

### Custom User Model
- Email-based authentication (no username)
- Located in `apps/accounts/models/users.py`
- Includes first_name, last_name, and standard Django permissions

### API Authentication
- JWT tokens via `rest_framework_simplejwt`
- Session authentication for browsable API
- Custom permissions with tenant support

## 🛠️ Extending the Project

### Adding New Apps
```bash
python manage.py startapp your_app_name apps/your_app_name
```

### Using Base Models
```python
from backend.core.models import BaseModel, BaseModelWithTenant

class YourModel(BaseModelWithTenant):
    name = models.CharField(max_length=100)
    # Automatically includes: id, created_at, updated_at, created_by, updated_by, tenant
```



## 🏢 Multi-Tenant Foundation

The SGTP repository includes the Supplier / Shop and membership foundation. Full request-context enforcement and cross-Shop isolation remain pending T3-03 and later Phase 3 tasks:

### Tenant Features
- **Tenant Model**: Technical representation of a Shop, owned by the single Main Supplier, with contact info and settings
- **Membership**: `TenantMember` and `ShopRolePolicy` define User-Shop membership and the current role policy
- **User Limits**: Configurable maximum users per tenant
- **Tenant Admin**: Full Django admin interface for tenant management
- **API Endpoints**: REST APIs for Shop/Tenant and membership operations; Main Supplier policy controls Shop writes
- **Tenant Base Model**: Models can inherit `BaseModelWithTenant`; full request context and business-record isolation remain pending Phase 3

### Shop (Tenant) and Membership API Endpoints
- `GET /api/v1/tenants/` - List Shops subject to the current API permissions
- `POST /api/v1/tenants/` - Create a Shop subject to Main Supplier policy
- `GET /api/v1/tenants/{id}/` - Retrieve a Shop subject to current API permissions
- `PUT/PATCH /api/v1/tenants/{id}/` - Update a Shop subject to current API permissions
- `POST /api/v1/tenants/{id}/activate/` and `/deactivate/` - Main Supplier-authorized lifecycle actions
- `GET /api/v1/tenants/{id}/stats/` - Shop statistics
- `/api/v1/memberships/` - User-Shop membership operations and lifecycle actions

### Using Tenant Models
```python
from backend.core.models import BaseModelWithTenant

class YourModel(BaseModelWithTenant):
    name = models.CharField(max_length=100)
    # Automatically includes tenant relationship and audit fields
```



## 📚 API Documentation

Access interactive API documentation:
- **Browsable API Explorer**: `/api/browse/` (active Main Supplier Django Admin session required; API calls use a manually entered JWT)
- **Swagger UI**: `/api/docs/` and **OpenAPI Schema**: `/api/schema/` (same access policy)
- The root URL redirects to the protected Browsable API portal. The committed `schema.yml` remains publicly readable from this public GitHub repository.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

If you encounter any issues or have questions, please create an issue in the repository.
