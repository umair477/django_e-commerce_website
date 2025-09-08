# Django E-commerce Website

A modern e-commerce website built with Django 5.2.4.

## Features

- User authentication and registration
- Product catalog with categories
- Shopping cart functionality
- Order management
- User profiles
- Email verification
- Password reset functionality

## Requirements

- Python 3.8+
- Django 5.2.4
- Pillow 10.2.0 (for image handling)
- python-decouple 3.8 (for environment variables)
- requests 2.31.0 (for HTTP requests)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd django_e-commerce_website-main
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Open your browser and navigate to `http://127.0.0.1:8000/`

## Project Structure

- `accounts/` - User authentication and profiles
- `category/` - Product categories
- `store/` - Product management
- `carts/` - Shopping cart functionality
- `orders/` - Order management
- `greatkart/` - Main project settings and configuration
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)

## Configuration

The project uses SQLite as the default database. For production, consider using PostgreSQL or MySQL.

Update the following settings in `greatkart/settings.py` for production:
- `DEBUG = False`
- `ALLOWED_HOSTS`
- `SECRET_KEY`
- Database configuration
- Email settings

## Email Configuration

Update the email settings in `greatkart/settings.py`:
```python
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
EMAIL_USE_TLS = True
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE). 