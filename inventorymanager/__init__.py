"""
This module is used to start and retrieve a Flask application complete with all the required setups
"""

import json
import os

from flasgger import Swagger
from flask import Flask, Response, send_from_directory
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy

from inventorymanager.config import Config
from inventorymanager.constants import LINK_RELATIONS_URL, MASON, NAMESPACE

db = SQLAlchemy()
cache = Cache()

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
    app.config["CACHE_TYPE"] = "FileSystemCache"
    if test_config is None or "CACHE_DIR" not in test_config:
        app.config["CACHE_DIR"] = os.path.join(app.instance_path, "cache")
    else:
        app.config["CACHE_DIR"] = test_config["CACHE_DIR"]

    cache.init_app(app)
    # CLI commands to populate db
    from inventorymanager.models import (create_dummy_data,
                                         generate_catalogue_key,
                                         init_db_command)

    app.cli.add_command(init_db_command)
    app.cli.add_command(create_dummy_data)
    app.cli.add_command(generate_catalogue_key)

    from inventorymanager.api import api_bp
    from inventorymanager.utils import (ItemConverter, LocationConverter,
                                        WarehouseConverter)

    app.url_map.converters["warehouse"] = WarehouseConverter
    app.url_map.converters["item"] = ItemConverter
    app.url_map.converters["location"] = LocationConverter
    app.register_blueprint(api_bp)

    # Static routes related to profiles and link relations
    # from sensorhub project example and Exercise 3 material on Lovelace
    @app.route("/profiles/<resource>/")
    def send_profile_html(resource):
        """
        Send the profile file
        :param resource: resource to send profile for
        """
        return send_from_directory(app.static_folder, f"profiles/{resource}.html")

    @app.route(LINK_RELATIONS_URL)
    def send_link_relations_html():
        """
        Send the link relations file
        """
        return send_from_directory(app.static_folder, "link-relations.html")

    from inventorymanager.builder import InventoryManagerBuilder

    @app.route("/api/")
    def api_entrypoint() -> Response:
        """
        Entrypoint to the API
        """
        body = InventoryManagerBuilder()
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control_all_catalogue()
        body.add_control_all_warehouses()
        body.add_control_all_items()
        body.add_control_all_stock()
        return Response(json.dumps(body), 200, mimetype=MASON)

    return app
