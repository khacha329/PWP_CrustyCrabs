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

from inventorymanager import db
from inventorymanager.constants import DOC_FOLDER
from inventorymanager.models import Location
from inventorymanager.utils import create_error_response


class LocationCollection(Resource):
    """Class for collection of warehouse locations including addresses.
    /locations/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/collection/get.yml")
    def get(self):
        """Gets all locations present in the database

        Returns:
            Array: List of all locations
        """
        body = []
        for location in Location.query.all():
            location_json = location.serialize()
            location_json["uri"] = url_for("api.locationitem", location=location)
            body.append(location_json)

        return Response(json.dumps(body), 200, mimetype="application/json")

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

        return Response(
            status=201,
            headers={"Location": url_for("api.locationitem", location=location)},
        )


class LocationItem(Resource):
    """Class for a location resource.
    /locations/<location:location>/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/item/get.yml")
    def get(self, location):
        """Retrieves location

        Args:
            location: location

        Returns:
            string: The matching location
        """
        location_entry = Location.query.filter_by(
            location_id=location.location_id
        ).first()
        location_json = location_entry.serialize()
        location_json["uri"] = url_for("api.locationitem", location=location)
        return Response(json.dumps(location_json), 200)

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

        return Response(status=204)
