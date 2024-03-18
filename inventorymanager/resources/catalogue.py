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
    /catalogue/
    """

    def get(self):
        """Returns a list of all catalogue entries in the database

        :return: Response
        """
        body = []
        for catalogue in Catalogue.query.all():

            catalogue_json = catalogue.serialize()
            catalogue_json["uri"] = url_for(
                "api.catalogueitem",
                supplier=catalogue.supplier_name,
                item=catalogue.item,
            )
            body.append(catalogue_json)

        return Response(json.dumps(body), 200)

    def post(self):
        try:
            validate(request.json, Catalogue.get_schema())
            item_entry = Item.query.filter_by(item_id=request.json["item_id"]).first()

            if not item_entry:
                return create_error_response(404, "Item doesn't exist")
            catalogue = Catalogue(item=item_entry)
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
                    item=catalogue.item,
                )
            },
        )


class CatalogueItem(Resource):
    """
    Resource for a single catalogue entry, provides GET, PUT and DELETE methods
    /catalogue/supplier/<string:supplier>/item/<item:item>/
    """

    def get(self, supplier, item):
        """returns a single catalogue entry in the database

        :param supplier: supplier name of the catalogue entry to return
        :param item: item name of the catalogue entry to return
        :return: Response
        """
        catalogue_entry = Catalogue.query.filter_by(
            supplier_name=supplier, item=item
        ).first()
        if not catalogue_entry:
            return create_error_response(404, "Catalogue entry doesn't exist")
        catalogue_json = catalogue_entry.serialize()
        catalogue_json["uri"] = url_for(
            "api.catalogueitem", supplier=supplier, item=item
        )
        return Response(json.dumps(catalogue_json), 200)

    def put(self, supplier, item):
        """updates a single catalogue entry in the database

        :param supplier: supplier name of the catalogue entry to update
        :param item: item name of the catalogue entry to update
        :return: Response
        """

        catalogue_entry = Catalogue.query.filter_by(
            supplier_name=supplier, item_id=item.item_id
        ).first()
        if not catalogue_entry:
            return create_error_response(404, "Catalogue entry doesn't exist")
        try:
            validate(request.json, Catalogue.get_schema())
            catalogue_entry.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            db.session.rollback()
            return create_error_response(400, "Invalid JSON document", str(e))

        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409,
                "Already exists",
                "catalogue with item '{}' from supplier '{}'already exists.".format(
                    request.json["item_id"], request.json["supplier_name"]
                ),
            )

        return Response(status=204)

    def delete(self, supplier, item):
        """deletes a single catalogue entry in the database

        :param supplier: supplier name of the catalogue entry to delete
        :param item: item name of the catalogue entry to delete
        :return: Response
        """

        # Retrieve the catalogue entry entry based item ID and supplier name
        catalogue_entry = Catalogue.query.filter_by(
            supplier_name=supplier, item=item
        ).first()
        if not catalogue_entry:
            return create_error_response(404, "Catalogue entry doesn't exist")
        db.session.delete(catalogue_entry)
        db.session.commit()

        return Response(status=204)


class CatalogueItemCollection(Resource):
    """
    Resource for the  ollection of catalogue entries filtered by item, provides GET method
    /catalogue/item/<item:item>/
    """

    def get(self, item: Item):
        """Returns a list of catalogue entries in the database filtered by item name

        :param item: item name to filter catalogue entry with
        :return: Response
        """

        body = []
        item = Item.query.filter_by(item_id=item.item_id).first()
        if not item:
            return create_error_response(404, "Item doesn't exist")

        catalogue_entry = Catalogue.query.filter_by(item_id=item.item_id).first()
        if not catalogue_entry:
            return create_error_response(404, "No supplier has the requested item")

        for catalogue in Catalogue.query.filter_by(item_id=item.item_id).all():
            catalogue_json = catalogue.serialize()
            catalogue_json["uri"] = url_for(
                "api.catalogueitem",
                supplier=catalogue.supplier_name,
                item=item,
            )
            body.append(catalogue_json)
        return Response(json.dumps(body), 200)


class CatalogueSupplierCollection(Resource):
    """
    Resource for the collection of catalogue entries filtered by supplier, provides GET method
    /catalogue/supplier/<string:supplier>/
    """

    def get(self, supplier: str):
        """Returns a list of catalogue entries in the database filtered by supplier name

        :param supplier: supplier name to filter catalogue entry with
        :return: Response
        """

        body = []
        catalogue_entry = Catalogue.query.filter_by(supplier_name=supplier).first()
        if not catalogue_entry:
            return create_error_response(404, "supplier does not exist")

        for catalogue in Catalogue.query.filter_by(supplier_name=supplier).all():
            catalogue_json = catalogue.serialize()
            catalogue_json["uri"] = url_for(
                "api.catalogueitem",
                supplier=catalogue.supplier_name,
                item=catalogue.item,
            )
            body.append(catalogue_json)
        return Response(json.dumps(body), 200)
