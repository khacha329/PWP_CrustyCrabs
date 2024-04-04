"""
This module contains the resources for the catalogue endpoints.
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
from inventorymanager.models import Catalogue, Item
from inventorymanager.constants import DOC_FOLDER
from inventorymanager.utils import create_error_response, request_path_cache_key
from inventorymanager.constants import (
    NAMESPACE,
    LINK_RELATIONS_URL,
    CATALOGUE_PROFILE,
    MASON
)

class CatalogueCollection(Resource):
    """
    Resource for the collection of catalogue entries, provides GET and POST methods
    /catalogue/
    """
    @swag_from(os.getcwd() + f"{DOC_FOLDER}catalogue/collection/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self):
        """Returns a list of all catalogue entries in the database

        :return: Response
        """
        body = InventoryManagerBuilder(catalogues=[])
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.cataloguecollection"))
        
        for catalogue_object in Catalogue.query.all():
            catalogue = InventoryManagerBuilder(catalogue_object.serialize())
            catalogue.add_control(
                "self",
                url_for("api.catalogueitem", supplier=catalogue_object.supplier_name, item=catalogue_object.item,),
            )
            catalogue.add_control("profile", CATALOGUE_PROFILE)
            body["catalogues"].append(catalogue)

        body.add_control_post(
            "add-catalogue",
            "Add new Catalogue",
            url_for("api.cataloguecollection"),
            Catalogue.get_schema()
        )

        body.add_control_all_items()

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}catalogue/collection/post.yml")
    def post(self):
        """Adds a new catalogue to the database

        :return: Response
        """
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
            db.session.rollback()
            return abort(400, e.message)

        except IntegrityError:
            db.session.rollback()
            return abort(409, "Catalogue already exists")
        # if api fails after this line, resource will be added to db anyway
        self._clear_cache()
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
    
    def _clear_cache(self):
        cache.delete(
            request.path
        )

class CatalogueItem(Resource):
    """
    Resource for a single catalogue entry, provides GET, PUT and DELETE methods
    /catalogue/supplier/<string:supplier>/item/<item:item>/
    """
    @swag_from(os.getcwd() + f"{DOC_FOLDER}catalogue/item/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
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
            return create_error_response(404, "supplier and item combination does not exist")

        self_url = url_for("api.catalogueitem", supplier=supplier, item=item)
        body = InventoryManagerBuilder(catalogue_entry.serialize())

        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("profile", CATALOGUE_PROFILE)
        body.add_control("collection", url_for("api.cataloguecollection"))
        body.add_control_put("Modify this catalogue item", self_url, Catalogue.get_schema())
        body.add_control_delete("Delete this catalogue item", self_url)
        body.add_control_get_item(item)
        body.add_control_all_catalogue_supplier(supplier)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}catalogue/item/put.yml")
    def put(self, supplier, item):
        """updates a single catalogue entry in the database

        :param supplier: supplier name of the catalogue entry to update
        :param item: item name of the catalogue entry to update
        :return: Response
        """
        item_entry = Item.query.filter_by(item_id=request.json["item_id"]).first()
        if not item_entry:
            return create_error_response(404, "Item doesn't exist")
        try:
            validate(request.json, Catalogue.get_schema())
            catalogue_entry = Catalogue.query.filter_by(
                supplier_name=supplier, item_id=item.item_id
            ).first()
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

        self._clear_cache()
        return Response(status=204)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}catalogue/item/delete.yml")
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

        self._clear_cache()
        return Response(status=204)
    
    def _clear_cache(self):
        collection_path = url_for("api.cataloguecollection")
        cache.delete_many(
            collection_path,
            request.path
        )


class CatalogueItemCollection(Resource):
    """
    Resource for the collection of catalogue entries filtered by item, provides GET method
    /catalogue/item/<item:item>/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}catalogue/itemcollection/get.yml")
    def get(self, item: Item):
        """Returns a list of catalogue entries in the database filtered by item name

        :param item: item name to filter catalogue entry with
        :return: Response
        """

        item = Item.query.filter_by(item_id=item.item_id).first()
        
        body = InventoryManagerBuilder(catalogues=[])
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.catalogueitemcollection", item=item))
        catalogue_entry = Catalogue.query.filter_by(item_id=item.item_id).first()
        if not catalogue_entry:
            return create_error_response(404, "No supplier has the requested item")

        for catalogue_obj in Catalogue.query.filter_by(item_id=item.item_id).all():
            catalogue = InventoryManagerBuilder(catalogue_obj.serialize())
            catalogue.add_control(
                "self",
                url_for("api.catalogueitem", supplier=catalogue_obj.supplier_name, item=catalogue_obj.item )     
            )
            catalogue.add_control("profile", CATALOGUE_PROFILE)
            body["catalogues"].append(catalogue)

        body.add_control_all_catalogue()
        
        return Response(json.dumps(body), 200, mimetype=MASON)


class CatalogueSupplierCollection(Resource):
    """
    Resource for the collection of catalogue entries filtered by supplier, provides GET method
    /catalogue/supplier/<string:supplier>/
    """
    
    @swag_from(os.getcwd() + f"{DOC_FOLDER}catalogue/suppliercollection/get.yml")
    def get(self, supplier: str):
        """Returns a list of catalogue entries in the database filtered by supplier name

        :param supplier: supplier name to filter catalogue entry with
        :return: Response
        """
        catalogue_entry = Catalogue.query.filter_by(supplier_name=supplier).first()
        if not catalogue_entry:
            return create_error_response(404, "supplier does not exist")
        
        self_url = url_for("api.cataloguesuppliercollection", supplier=supplier)
        body = InventoryManagerBuilder(catalogues=[])
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)
 
        for catalogue in Catalogue.query.filter_by(supplier_name=supplier).all():
            supplier_catalogue = InventoryManagerBuilder(catalogue.serialize())
            supplier_catalogue.add_control(
                "self",
                url_for("api.catalogueitem", supplier=catalogue.supplier_name, item=catalogue.item),
            )
            supplier_catalogue.add_control("profile", CATALOGUE_PROFILE)
            body["catalogues"].append(supplier_catalogue)
        
        body.add_control_all_catalogue()

        return Response(json.dumps(body), 200, mimetype=MASON)
    