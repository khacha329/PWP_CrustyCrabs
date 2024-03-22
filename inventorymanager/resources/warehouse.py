"""
This module contains the resources for the warehouse endpoints.
"""

import json

from flask import Response, abort, request, url_for
from flask_restful import Resource
from jsonschema import validate
from sqlalchemy.exc import IntegrityError

from inventorymanager import db, cache
from inventorymanager.models import Warehouse
from inventorymanager.utils import create_error_response, request_path_cache_key


class WarehouseCollection(Resource):
    """
    Resource for the collection of warehouses, provides GET and POST methods
    /warehouses/
    """
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self):
        """Returns a list of all warehouses in the database

        :return: Response
        """
        body = []
        for warehouse in Warehouse.query.all():
            warehouse_json = warehouse.serialize()
            warehouse_json["uri"] = url_for("api.warehouseitem", warehouse=warehouse)
            body.append(warehouse_json)

        return Response(json.dumps(body), 200)

    def post(self):
        """Adds a new warehouse to the database

        :return: Response
        """
        try:
            validate(request.json, Warehouse.get_schema())
            warehouse = Warehouse()
            warehouse.deserialize(request.json)

            db.session.add(warehouse)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            return abort(409, "Warehouse already exists")

        self._clear_cache()
        return Response(
            status=201,
            headers={"Location": url_for("api.warehouseitem", warehouse=warehouse)},
        )

    def _clear_cache(self):
        cache.delete(
            request.path
        )

class WarehouseItem(Resource):
    """
    Resource for a single warehouse, provides GET, PUT and DELETE methods
    /warehouses/<warehouse:warehouse>/
    """
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, warehouse):
        """returns a single warehouse in the database with its location details

        :param warehouse: warehouse id of the warehouse to return
        :return: Response
        """

        location = warehouse.location
        location_json = location.serialize()
        # Retrieve the stock entry based on warehouse ID and item ID
        warehouse_json = warehouse.serialize()
        warehouse_json["uri"] = url_for("api.warehouseitem", warehouse=warehouse)
        body = []
        body.append(warehouse_json)
        body.append(location_json)
        return Response(json.dumps(body), 200)

    def put(self, warehouse: Warehouse):
        """updates a single warehouse in the database

        :param warehouse: warehouse
        :return: Response
        """
        try:
            validate(request.json, Warehouse.get_schema())
            warehouse.deserialize(request.json)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409,
                "Already exists",
                "warehouse with id '{}' already exists.".format(
                    request.json["warehouse_id"]
                ),
            )

        self._clear_cache()
        return Response(status=204)

    def delete(self, warehouse: Warehouse):
        """deletes a single warehouse in the database

        :param warehouse: warehouse id of the warehouse to delete
        :return: Response
        """
        db.session.delete(warehouse)
        db.session.commit()

        self._clear_cache()
        return Response(status=204)

    def _clear_cache(self):
        collection_path = url_for("api.warehousecollection ")
        cache.delete_many(
            collection_path,
            request.path
        )