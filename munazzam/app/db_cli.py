import click
from flask.cli import with_appcontext
from . import db
# Import models here to ensure they are registered with SQLAlchemy before table creation
from . import models

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    # The 'db' object is the SQLAlchemy instance from __init__.py
    # db.create_all() creates tables based on all defined models
    db.create_all()
    click.echo('Initialized the database.')

def init_app(app):
    """Register database functions with the Flask app."""
    app.cli.add_command(init_db_command)
