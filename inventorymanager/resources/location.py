"""
Code edited from course example
https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/location.py
Examples from PWP course exercise 2
https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/#dynamic-schemas-static-methods
"""

import json
import os

from flasgger import swag_from
from flask import Response, abort, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError

from inventorymanager import db, cache
from inventorymanager.builder import InventoryManagerBuilder
from inventorymanager.constants import (
    DOC_FOLDER, 
    NAMESPACE,
    LINK_RELATIONS_URL,
    LOCATION_PROFILE,
    MASON
)
from inventorymanager.models import Location
from inventorymanager.utils import request_path_cache_key


class LocationCollection(Resource):
    """Class for collection of warehouse locations including addresses.
    /locations/
    """
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/collection/get.yml")
    def get(self):
        """Gets all locations present in the database

        Returns:
            Array: List of all locations
        """
        self_url = url_for("api.locationcollection")
        body = InventoryManagerBuilder(locations=[])
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)

        for location_object in Location.query.all():
            location = InventoryManagerBuilder(location_object.serialize())
            location.add_control("self", url_for("api.locationitem", location=location_object))
            location.add_control("profile", LOCATION_PROFILE)
            body["locations"].append(location)

        body.add_control_post(
            "add-location", 
            "Add new location",
            url_for("api.locationcollection"), 
            Location.get_schema()
        )

        body.add_control_all_warehouses()

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/collection/post.yml")
    def post(self):
        """Add a new location to the database

        Returns:
            Response: A response object containing the URI of the new location in the header
        """
        try:
            validate(request.json, Location.get_schema())
            location = Location()
            location.deserialize(request.json)

            db.session.add(location)
            db.session.commit()

        except ValidationError as e:
            return {"message": "Validation error", "errors": str(e)}, 400

        except IntegrityError:
            db.session.rollback()
            return {"message": "Location already exists"}, 409

        self._clear_cache()
        
        return Response(
            status=201,
            headers={"Location": url_for("api.locationitem", location=location)},
        )

    def _clear_cache(self):
        cache.delete(
            request.path
        )


class LocationItem(Resource):
    """Class for a location resource.
    /locations/<location:location>/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/item/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, location: Location) -> Response:
        """Retrieves location

        Args:
            location: location

        Returns:
            string: The matching location
            
        """
        location_entry = Location.query.filter_by(
            location_id=location.location_id
        ).first()
        self_url = url_for("api.locationitem", location=location_entry)
        body = InventoryManagerBuilder(location_entry.serialize())

        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("profile", LOCATION_PROFILE)
        body.add_control("collection", url_for("api.locationcollection"))
        body.add_control_put("Modify this Location", self_url, Location.get_schema())
        body.add_control_delete("Delete this Location", self_url)
        body.add_control_get_warehouse(warehouse=location.warehouse)

        # location_entry = Location.query.filter_by(
        #     location_id=location.location_id
        # ).first()
        # location_json = location_entry.serialize()
        # location_json["uri"] = url_for("api.locationitem", location=location)
        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/item/put.yml")
    def put(self, location):
        """
        Updates existing location_id. Validates against JSON schema.

        Args:
            location : location

        """
        if not request.is_json:
            return {"message": "Request must be JSON"}, 415

        data = request.get_json()

        try:
            validate(instance=data, schema=Location.get_schema())
            location.deserialize(data)
            db.session.add(location)
            db.session.commit()
        except ValidationError as e:
            db.session.rollback()
            return abort(400, e.message)

        except IntegrityError:
            db.session.rollback()
            return abort(409, "stock already exists")
        
        self._clear_cache()
        return {}, 204

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/item/delete.yml")
    def delete(self, location):
        """
        Deletes existing location. Returns status code 204 if deletion is successful.

        Args:
            location: location

        """
        db.session.delete(location)
        db.session.commit()

        self._clear_cache()
        return Response(status=204)

    def _clear_cache(self):
        collection_path = url_for("api.locationcollection")
        cache.delete_many(
            collection_path,
            request.path
        )