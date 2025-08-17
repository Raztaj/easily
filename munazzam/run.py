from app import create_app

# Create the Flask app instance using the factory
app = create_app()

if __name__ == '__main__':
    # The app.run() method is suitable for development.
    # For production, a proper WSGI server like Gunicorn or uWSGI should be used.
    app.run(debug=True)
