import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize the database extension
db = SQLAlchemy()

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)

    # Set default configuration
    db_path = os.path.join(app.instance_path, 'munazzam.sqlite')
    app.config.from_mapping(
        SECRET_KEY='dev',  # Change this for production
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.update(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)

    # Import and register database commands
    from . import db_cli
    db_cli.init_app(app)

    # Import and register the blueprint
    from . import routes
    app.register_blueprint(routes.bp)
    app.add_url_rule('/', endpoint='index')

    return app
