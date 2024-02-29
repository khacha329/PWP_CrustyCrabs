"""
This module is used to start and retrieve a Flask application complete with all the required setups
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

from inventorymanager.config import Config

db = SQLAlchemy()

# Structure learned from the following sources:
# https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/quickstart/
# https://www.digitalocean.com/community/tutorials/how-to-structure-a-large-flask-application-with-flask-blueprints-and-flask-sqlalchemy#the-target-application-structure
# https://www.digitalocean.com/community/tutorials/how-to-use-flask-sqlalchemy-to-interact-with-databases-in-a-flask-application#step-2-setting-up-the-database-and-model


def create_app(test_config=None):
    
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # CACHE_TYPE="FileSystemCache",
        # CACHE_DIR=os.path.join(app.instance_path, "cache"),
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    
    except OSError:
        pass

    db.init_app(app)
    app.app_context().push()

    #cache.init_app(app)

    # Import All Models (not sure why yet, its a thing-to-do to make this work)
    from inventorymanager.models import Location, Warehouse, Item, Stock, Catalogue

    # CLI commands to populate db
    from inventorymanager.models import init_db_command, create_dummy_data

    app.cli.add_command(init_db_command)
    app.cli.add_command(create_dummy_data)

    from inventorymanager.api import api_bp
    from inventorymanager.utils import WarehouseConverter, ItemConverter, CatalogueConverter, StockConverter
    app.url_map.converters["warehouse"] = WarehouseConverter
    app.url_map.converters["catalogue"] = CatalogueConverter
    app.url_map.converters["stock"] = StockConverter
    app.url_map.converters["item"] = ItemConverter
    app.register_blueprint(api_bp)

    return app
