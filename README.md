# Jhaytermax Backend

Django REST API backend for the Jhaytermax e-commerce platform.

## Features

- 🛒 **Product Management**: CRUD operations for products and categories
- 👤 **User Authentication**: JWT-based authentication with role-based access
- 📦 **Order Management**: Complete order lifecycle with status tracking
- 💳 **Payment Integration**: Flutterwave payment gateway integration
- 📍 **Location System**: State and location-based delivery fee calculation
- 👨‍💼 **Admin Dashboard**: Comprehensive admin interface for management
- 🔒 **Security**: CORS, CSRF protection, and secure settings

## Tech Stack

- **Framework**: Django 4.2.7
- **API**: Django REST Framework
- **Authentication**: JWT (Simple JWT)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Payments**: Flutterwave
- **Deployment**: PythonAnywhere

## Project Structure

```
jhaytermax-backend/
├── config/                 # Django settings
│   ├── settings.py        # Development settings
│   ├── settings_prod.py   # Production settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI application
├── accounts/              # User authentication app
├── products/              # Product management app
├── orders/                # Order management app
├── payments/              # Payment processing app
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
├── env-sample.txt        # Environment variables template
└── deploy.sh            # Deployment script
```

## Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Pheebemi/jhaytermax-backend.git
   cd jhaytermax-backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env-sample.txt .env
   # Edit .env with your local configuration
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server:**
   ```bash
   python manage.py runserver
   ```

8. **Access the API:**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - API Docs: http://localhost:8000/swagger/ or http://localhost:8000/redoc/

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/refresh/` - Refresh JWT token

### Products
- `GET /api/products/` - List products
- `GET /api/products/{id}/` - Get product details
- `GET /api/categories/` - List categories

### Orders
- `GET /api/orders/` - List user orders (authenticated)
- `POST /api/orders/` - Create new order (authenticated)
- `GET /api/orders/{id}/` - Get order details (authenticated)
- `GET /api/states/` - List states
- `GET /api/locations/` - List locations

### Payments
- `POST /api/payments/initiate/` - Initiate payment (authenticated)
- `POST /api/payments/verify/` - Verify payment status
- `POST /api/payments/webhook/` - Flutterwave webhook

### Admin Only
- Full CRUD operations for products, categories, orders
- User management
- Payment monitoring

## Environment Variables

Create a `.env` file with the following variables:

```env
# Django Configuration
SECRET_KEY=your-secret-key
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings

# Flutterwave Configuration
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK_TEST-xxxxxxxxxxxxx
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-xxxxxxxxxxxxx
FLUTTERWAVE_ENCRYPTION_KEY=FLWSECK_TESTxxxxxxxxx
FLUTTERWAVE_SECRET_HASH=your_webhook_secret_hash
FLUTTERWAVE_SANDBOX=True
FLUTTERWAVE_REDIRECT_URL=http://localhost:3000/payment/callback

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Deployment

See [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) for detailed deployment instructions to PythonAnywhere.

### Quick Deployment

```bash
# Run the automated deployment script
./deploy.sh

# Configure environment
cp env-sample.txt .env
# Edit .env with production values

# Follow the deployment guide for PythonAnywhere configuration
```

## Testing

```bash
# Run tests
python manage.py test

# Run with coverage
pip install coverage
coverage run manage.py test
coverage report
```

## API Documentation

The API documentation is automatically generated using drf-yasg:

- **Swagger UI**: `/swagger/`
- **ReDoc**: `/redoc/`

## Security Features

- JWT authentication with refresh tokens
- CORS protection
- CSRF protection
- Input validation and sanitization
- Secure password hashing
- Rate limiting (configurable)
- SSL/TLS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation
- Review the deployment guide for common issues