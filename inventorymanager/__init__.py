"""
This module is used to start and retrieve a Flask application complete with all the required setups
"""

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger

from inventorymanager.config import Config

db = SQLAlchemy()

# Structure learned from the following sources:
# https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/quickstart/
# https://www.digitalocean.com/community/tutorials/how-to-structure-a-large-flask-application-with-flask-blueprints-and-flask-sqlalchemy#the-target-application-structure
# https://www.digitalocean.com/community/tutorials/how-to-use-flask-sqlalchemy-to-interact-with-databases-in-a-flask-application#step-2-setting-up-the-database-and-model


def create_app(test_config=None) -> Flask:
    """creates app from config file if specified

    :param test_config: test configuration, defaults to None
    :return: app for Flask application
    """

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///"
        + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # CACHE_TYPE="FileSystemCache",
        # CACHE_DIR=os.path.join(app.instance_path, "cache"),
    )

    app.config["SWAGGER"] = {
        "title": "InventoryManger API",
        "openapi": "3.0.3",
        "uiversion": 3,
    }

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

    # Swagger 
    Swagger(app, template_file="doc/hub.yml")

    # Cache Initialization


    # CLI commands to populate db
    from inventorymanager.models import create_dummy_data, init_db_command

    app.cli.add_command(init_db_command)
    app.cli.add_command(create_dummy_data)

    from inventorymanager.api import api_bp
    from inventorymanager.utils import (CatalogueConverter, ItemConverter,
                                        LocationConverter, StockConverter,
                                        WarehouseConverter)

    app.url_map.converters["warehouse"] = WarehouseConverter
    app.url_map.converters["catalogue"] = CatalogueConverter
    app.url_map.converters["stock"] = StockConverter
    app.url_map.converters["item"] = ItemConverter
    app.url_map.converters["location"] = LocationConverter
    app.register_blueprint(api_bp)

    return app
