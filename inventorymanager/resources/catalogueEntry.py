import json

from flask import Response, abort, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError

from inventorymanager import db
from inventorymanager.constants import *
from inventorymanager.models import Catalogue, Item
from inventorymanager.utils import create_error_response


class CatalogueCollection(Resource):
    """
    Resource for the collection of catalogue entries, provides GET and POST methods
    """
    def get(self):
        """Returns a list of all catalogue entries in the database

        :return: Response
        """
        body = []
        for catalogue in Catalogue.query.all():
            item = Item.query.filter_by(item_id=catalogue.item_id).first()
            catalogue_json = catalogue.serialize()
            catalogue_json["uri"] = url_for(
                "api.catalogueitem", supplier=catalogue.supplier_name, item=item.name
            )
            body.append(catalogue_json)

        return Response(json.dumps(body), 200)

    def post(self):
        """Adds a new catalogue entry to the database

        :return: Response
        """
        try:
            validate(request.json, Catalogue.get_schema())
            item_name = request.json["item_name"]
            item_entry = Item.query.filter_by(name=item_name).first()

            if not item_entry:
                return create_error_response(404, "Item doesn't exist")
            catalogue = Catalogue(item_id=item_entry.item_id)
            catalogue.deserialize(request.json)

            db.session.add(catalogue)
            db.session.commit()

        except ValidationError as e:
            return abort(400, e.message)

        except IntegrityError:
            return abort(409, "Catalogue already exists")
        # if api fails after this line, resource will be added to db anyway
        return Response(
            status=201,
            headers={
                "Location": url_for(
                    "api.catalogueitem",
                    supplier=catalogue.supplier_name,
                    item=item_entry.name,
                )
            },
        )


class CatalogueItem(Resource):
    """
    Resource for a single catalogue entry, provides GET, PUT and DELETE methods
    """
    def get(self, supplier, item):
        """returns a single catalogue entry in the database

        :param supplier: supplier name of the catalogue entry to return
        :param item: item name of the catalogue entry to return
        :return: Response
        """
        item_name = item.replace("_", " ")
        item = Item.query.filter_by(name=item_name).first()
        supplier_name = supplier.replace("_", " ")

        if not item:
            return create_error_response(404, "Item doesn't exist")
        catalogue_entry = Catalogue.query.filter_by(
            supplier_name=supplier_name, item_id=item.item_id
        ).first()
        if not catalogue_entry:
            return create_error_response(404, "Catalogue entry doesn't exist")
        catalogue_json = catalogue_entry.serialize()
        catalogue_json["uri"] = url_for(
            "api.catalogueitem", supplier=supplier_name, item=item.name
        )
        return Response(json.dumps(catalogue_json), 200)

    def put(self, supplier, item):
        """updates a single catalogue entry in the database

        :param supplier: supplier name of the catalogue entry to update
        :param item: item name of the catalogue entry to update
        :return: Response
        """
        item_name = item.replace("_", " ")
        item = Item.query.filter_by(name=item_name).first()
        supplier_name = supplier.replace("_", " ")
        if not item:
            return create_error_response(404, "Item doesn't exist")
        catalogue_entry = Catalogue.query.filter_by(
            supplier_name=supplier_name, item_id=item.item_id
        ).first()
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
                409,
                "Already exists",
                "Catalogue with name '{}' already exists.".format(request.json["name"]),
            )

        return Response(status=204)

    def delete(self, supplier, item):
        """deletes a single catalogue entry in the database

        :param supplier: supplier name of the catalogue entry to delete
        :param item: item name of the catalogue entry to delete
        :return: Response
        """
        item_name = item.replace("_", " ")
        item = Item.query.filter_by(name=item_name).first()
        supplier_name = supplier.replace("_", " ")
        if not item:
            return create_error_response(404, "Item doesn't exist")

        # Retrieve the catalogue entry entry based item ID and supplier name
        catalogue_entry = Catalogue.query.filter_by(
            supplier_name=supplier_name, item_id=item.item_id
        ).first()
        if not catalogue_entry:
            return create_error_response(404, "Catalogue entry doesn't exist")
        db.session.delete(catalogue_entry)
        db.session.commit()

        return Response(status=204)


class ItemList(Resource):
    """
    Resource for the collection of catalogue entries filtered by item, provides GET method
    """
    def get(self, item):
        """Returns a list of catalogue entries in the database filtered by item name
        
        :param item: item name to filter catalogue entry with
        :return: Response
        """
        item_name = item.replace("_", " ")
        item = Item.query.filter_by(name=item_name).first()

        if not item:
            return create_error_response(404, "Item doesn't exist")
        body = []
        for catalogue_entry in Catalogue.query.filter_by(item_id=item.item_id).all():
            catalogue_json = catalogue_entry.serialize()
            catalogue_json["uri"] = url_for(
                "api.catalogueitem",
                supplier=catalogue_entry.supplier_name,
                item=item.name,
            )
            body.append(catalogue_json)
        return Response(json.dumps(body), 200)


class SupplierItemList(Resource):
    """
    Resource for the collection of catalogue entries filtered by supplier, provides GET method
    """
    def get(self, supplier):
        """Returns a list of catalogue entries in the database filtered by supplier name
        
        :param supplier: supplier name to filter catalogue entry with
        :return: Response
        """
        supplier = supplier.replace("_", " ")

        if not supplier:
            return create_error_response(400, "Item doesn't exist")
        body = []
        for catalogue_entry in Catalogue.query.filter_by(supplier_name=supplier).all():
            item = Item.query.filter_by(item_id=catalogue_entry.item_id).first()
            catalogue_json = catalogue_entry.serialize()
            catalogue_json["uri"] = url_for(
                "api.catalogueitem",
                supplier=catalogue_entry.supplier_name,
                item=item.name,
            )
            body.append(catalogue_json)
        return Response(json.dumps(body), 200)
