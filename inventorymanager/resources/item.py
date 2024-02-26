import json
from jsonschema import validate, ValidationError
from flask import Response, abort, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from inventorymanager.models import Item
from inventorymanager import db
from inventorymanager.constants import *
from inventorymanager.utils import create_error_response


class ItemCollection(Resource):
    

    def get(self):
        body = []
        for item in Item.query.all():
            item_json = item.serialize()
            item_json["uri"] = url_for("api.itemitem", item=item)
            body.append(item_json)

        return Response(json.dumps(body), 200)


    def post(self):
        try:
            validate(request.json, Item.get_schema())
            item = Item()
            item.deserialize(request.json)
        
            db.session.add(item)
            db.session.commit()

        except ValidationError as e:
            return abort(400, e.message)

        except IntegrityError:
            return abort(409, "Item already exists")

        return Response(status=201, headers={
            "Location": url_for("api.itemitem", item=item)
        })
    



class ItemItem(Resource):
    
    def get(self, item):
        pass

    def put(self, item : Item):
        try:
            validate(request.json, Item.get_schema())
            item.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
            
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Item with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=204)

    def delete(self, item : Item):
        db.session.delete(item)
        db.session.commit()

        return Response(status=204) 