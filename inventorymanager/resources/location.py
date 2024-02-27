
"""Code edited from course example 
https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/sensorhub/resources/location.py"""


import json

from flask import Response, abort, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate

from inventorymanager import db
from inventorymanager.models import Location

#from inventorymanager.constants import *



class LocationCollection(Resource):

    def get(self):
        body = []
        for location in Location.query.all():
            location_json = location.serialize()
            location_json["uri"] = url_for("api.locationitem", location_id=location.location_id, _external=True)
            body.append(location_json)

        return Response(json.dumps(body), 200, mimetype='application/json')

    def post(self):
        try:
            validate(request.json, Location.get_schema())
            location = Location()
            location.deserialize(request.json)
        
            db.session.add(location)
            db.session.commit()

        except ValidationError as e:
            return abort(400, e.message)

        except IntegrityError: #Does this make it so there cant be another location that matches all fields exactly or can there be same street name, different address etc
            return abort(409, "Location already exists")

        return Response(status=201, headers={
            "Location": url_for("api.locationitem", location=location)
        })
        pass


class LocationItem(Resource):

    def get(self, location_id):
        location = Location.query.get(location_id)
        if not location:
            return {"message": "Location not found"}, 404
        return location.serialize(), 200

    def post(self, location): #should this be PUT instead?
        def post(self):
        data = request.get_json(force=True)

        try:
            validate(instance=data, schema=Location.get_schema())
        except ValidationError as e:
            return {'message': 'Validation error', 'errors': str(e)}, 400

        new_location = Location()
        new_location.deserialize(data)

        db.session.add(new_location)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {'message': 'Database error', 'errors': str(e)}, 500

        return jsonify({
            'message': 'Location created successfully',
            'location': new_location.serialize(),
            'links': {
                'self': url_for('api.locationitem', location_id=new_location.location_id, _external=True)
            }
        }), 201



    
  # class SensorItem(Resource):

    # @cache.cached()
    # def get(self, sensor):
        # db_sensor = Sensor.query.filter_by(name=sensor).first()
        # if db_sensor is None:
            # raise NotFound
        # body = {
            # "name": db_sensor.name,
            # "model": db_sensor.model,
            # "location": db_sensor.location.description
        # }
        # return Response(json.dumps(body), 200, mimetype=JSON)