import json
from jsonschema import validate, ValidationError
from flask import Response, abort, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from inventorymanager.models import Catalogue, Item, require_admin_key
from inventorymanager import db
from inventorymanager.constants import *
from inventorymanager.utils import create_error_response



class CatalogueCollection(Resource):
    def get(self):
        body = []
        for catalogue in Catalogue.query.all():
            item = Item.query.filter_by(item_id=catalogue.item_id).first()
            catalogue_json = catalogue.serialize()
            catalogue_json["uri"] = url_for("api.catalogueitem", supplier=catalogue.supplier_name, item=item.name)
            body.append(catalogue_json)

        return Response(json.dumps(body), 200)
    
    @require_admin_key
    def post(self):
        try:
            validate(request.json, Catalogue.get_schema())
            item_name = request.json['item_name']
            item_entry = Item.query.filter_by(name=item_name).first()

            if not item_entry:
                return create_error_response(404, "Item doesn't exist")
            catalogue = Catalogue(item_id = item_entry.item_id)
            catalogue.deserialize(request.json)
        
            db.session.add(catalogue)
            db.session.commit()
            
        except ValidationError as e:
            return abort(400, e.message)

        except IntegrityError:
            return abort(409, "Catalogue already exists")
        #if api fails after this line, resource will be added to db anyway
        return Response(status=201, headers={
            "Location": url_for("api.catalogueitem", supplier=catalogue.supplier_name, item=item_entry.name)
        })

class CatalogueItem(Resource):
    def get(self, supplier, item):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()
        supplier_name = supplier.replace('_', ' ')

        if not item:
            return create_error_response(404, "Item doesn't exist")
        catalogue_entry = Catalogue.query.filter_by(supplier_name=supplier_name, item_id=item.item_id).first()
        if not catalogue_entry:
            return create_error_response(404, "Catalogue entry doesn't exist")
        catalogue_json = catalogue_entry.serialize()
        catalogue_json["uri"] = url_for("api.catalogueitem", supplier=supplier_name, item=item.name)       
        return Response(json.dumps(catalogue_json), 200)
    
    @require_admin_key
    def put(self, supplier, item):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()
        supplier_name = supplier.replace('_', ' ')
        if not item:
            return create_error_response(404, "Item doesn't exist")
        catalogue_entry = Catalogue.query.filter_by(supplier_name=supplier_name, item_id=item.item_id).first()
        if not catalogue_entry:
            return create_error_response(404, "Catalogue entry doesn't exist")
        try:
            validate(request.json, Catalogue.get_schema())
            catalogue_entry.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
            
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Catalogue with name '{}' already exists.".format(request.json["name"])
            )

        return Response(status=204)

    @require_admin_key
    def delete(self, supplier, item):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()
        supplier_name = supplier.replace('_', ' ')
        if not item:
            return create_error_response(404, "Item doesn't exist")

        #Retrieve the catalogue entry entry based item ID and supplier name
        catalogue_entry = Catalogue.query.filter_by(supplier_name=supplier_name, item_id=item.item_id).first()
        if not catalogue_entry:
            return create_error_response(404, "Catalogue entry doesn't exist")
        db.session.delete(catalogue_entry)
        db.session.commit()

        return Response(status=204)  
    
class ItemList(Resource):
    def get(self, item):
        item_name = item.replace('_', ' ')
        item = Item.query.filter_by(name=item_name).first()

        if not item:
            return create_error_response(404, "Item doesn't exist")
        body = []
        for catalogue_entry in Catalogue.query.filter_by(item_id=item.item_id).all():
            catalogue_json = catalogue_entry.serialize()
            catalogue_json["uri"] = url_for("api.catalogueitem", supplier=catalogue_entry.supplier_name, item=item.name)
            body.append(catalogue_json)
        return Response(json.dumps(body), 200)

    
class SupplierItemList(Resource):
    def get(self, supplier):
        supplier = supplier.replace('_', ' ')

        if not supplier:
            return create_error_response(400, "Item doesn't exist")
        body = []
        for catalogue_entry in Catalogue.query.filter_by(supplier_name=supplier).all():
            item = Item.query.filter_by(item_id=catalogue_entry.item_id).first()
            catalogue_json = catalogue_entry.serialize()
            catalogue_json["uri"] = url_for("api.catalogueitem", supplier=catalogue_entry.supplier_name, item=item.name)
            body.append(catalogue_json)
        return Response(json.dumps(body), 200)