# Django E-commerce Website

A full-featured e-commerce website built with Django, featuring product management, user authentication, shopping cart, payment integration, and more.

## Features

- User Authentication and Authorization
- Product Catalog with Categories
- Shopping Cart Functionality
- Payment Integration (Stripe, Razorpay, PayPal)
- Order Management
- Blog System
- Product Recommendations
- Responsive Design

## Tech Stack

- Django 5.1.7
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Bootstrap
- JavaScript

## Local Development Setup

1. Clone the repository
```bash
git clone <your-repo-url>
cd <repository-name>
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file in the root directory and add:
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create superuser
```bash
python manage.py createsuperuser
```

7. Run the development server
```bash
python manage.py runserver
```

## Deployment

This project is configured for deployment on Render.com. The `render.yaml` file contains all necessary deployment configurations.

To deploy:
1. Fork this repository
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Render will automatically deploy your application

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 