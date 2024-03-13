"""
Code edited from course example
https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/location.py
Examples from PWP course exercise 2
https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/implementing-rest-apis-with-flask/#dynamic-schemas-static-methods
"""
import os
import json

from flask import Response, request, url_for
from flask_restful import Resource
from flasgger import swag_from
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError

from inventorymanager import db
from inventorymanager.models import Location
from inventorymanager.constants import DOC_FOLDER

from inventorymanager.utils import create_error_response


class LocationCollection(Resource):
    """
    Class for collection of warehouse locations including addresses. /api/Locations/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/collection/get.yml")
    def get(self):
        """Gets all locations present in the database

        :return: List of all locations
        """
        body = []
        for location in Location.query.all():
            location_json = location.serialize()
            location_json["uri"] = url_for(
                "api.locationitem", location_id=location.location_id, _external=True
            )
            body.append(location_json)

        return Response(json.dumps(body), 200, mimetype="application/json")

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/collection/post.yml")
    def post(self):
        """Add a new location to the database

        :return: A response object containing the URI of the new location in the header
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

        location_uri = url_for(
            "api.locationitem", location_id=location.location_id, _external=True
        )
        response = Response(status=201)
        response.headers["Location"] = location_uri
        return response


class LocationItem(Resource):
    """Class for a location resource. '/api/Locations/location_id/'"""

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/item/get.yml")   
    def get(self, location_id):
        """Retrieves location matching to the provided location_id

        :param location_id: Unique identifier of the location
        :return: string: The matching location
        """
        location = Location.query.get(location_id)
        if not location:
            return {"message": "Location not found"}, 404
        return location.serialize(), 200

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/item/put.yml")   
    def put(self, location_id):
        """Updates existing location_id. Validates against JSON schema.

        :param location_id: Unique identifier of the location
        :return: location_id: Updated location_id
        """
        if not request.is_json:
            return {"message": "Request must be JSON"}, 415

        data = request.get_json()
        try:
            validate(instance=data, schema=Location.get_schema())
        except ValidationError as e:
            return {"message": "Validation error", "errors": str(e)}, 400

        location = Location.query.get(location_id)
        if not location:
            return {"message": "Location not found"}, 404

        location.deserialize(data)

        try:
            db.session.add(location)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"message": "Database error", "errors": str(e)}, 500

        return {}, 204

    @swag_from(os.getcwd() + f"{DOC_FOLDER}location/item/delete.yml")   
    def delete(self, location_id):
        """Deletes existing location. Returns status code 204 if deletion is successful.

        :param location_id: Unique identifier of the location
        :return: status code 204 if deletion is successful
        """
        location = Location.query.get(location_id)
        if not location:
            return {"message": "Location not found"}, 404
        db.session.delete(location)
        db.session.commit()

        return Response(status=204)
