import json
from jsonschema import validate, ValidationError
from flask import Response, abort, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from inventorymanager.models import Catalogue
from inventorymanager import db
from inventorymanager.constants import *
from inventorymanager.utils import create_error_response


class CatalogueCollection(Resource):
    

    def get(self):
        body = []
        for catalogue in Catalogue.query.all():
            catalogue_json = catalogue.serialize()
            catalogue_json["uri"] = url_for("api.cataloguecollection", catalogue=catalogue)
            body.append(catalogue_json)

        return Response(json.dumps(body), 200)


    def post(self):
        try:
            validate(request.json, Catalogue.get_schema())
            catalogue = Catalogue()
            catalogue.deserialize(request.json)
        
            db.session.add(catalogue)
            db.session.commit()
            
        except ValidationError as e:
            return abort(400, e.message)

        except IntegrityError:
            return abort(409, "Catalogue already exists")
        #if api fails after this line, resource will be added to db anyway
        return Response(status=201, headers={
            "Location": url_for("api.cataloguecollection", catalogue=catalogue)
        })
    



class CatalogueManagement(Resource):
    
    def get(self, catalogue):
        pass
        #This queries Catalogue by id. maybe change it to query by name or smthg?
    def put(self, catalogue : Catalogue):
        try:
            validate(request.json, Catalogue.get_schema())
            Catalogue.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
            
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Catalogue with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=204)

    def delete(self, catalogue : Catalogue):
        db.session.delete(catalogue)
        db.session.commit()

        return Response(status=204) 