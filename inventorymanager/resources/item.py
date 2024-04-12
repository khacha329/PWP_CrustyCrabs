""" Item resource module """

import json
import os

from flasgger import swag_from
from flask import Response, abort, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError

from inventorymanager import cache, db
from inventorymanager.builder import InventoryManagerBuilder
from inventorymanager.constants import (DOC_FOLDER, ITEM_PROFILE,
                                        LINK_RELATIONS_URL, MASON, NAMESPACE)
from inventorymanager.models import Item
from inventorymanager.utils import (create_error_response,
                                    request_path_cache_key)


class ItemCollection(Resource):
    """
    Resource for the collection of items, provides GET and POST methods
    /items/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}item/collection/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self) -> Response:
        """Returns a list of all items in the database

        :return: Response
        """

        body = InventoryManagerBuilder(items=[])
        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.itemcollection"))

        for item_object in Item.query.all():
            item = InventoryManagerBuilder(item_object.serialize())
            item.add_control("self", url_for("api.itemitem", item=item_object))
            item.add_control("profile", ITEM_PROFILE)
            body["items"].append(item)

        body.add_control_post(
            "add-item", "Add new item", url_for("api.itemcollection"), Item.get_schema()
        )
        body.add_control_all_catalogue()
        body.add_control_all_stock()

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}item/collection/post.yml")
    def post(self) -> Response:
        """Adds a new item to the database

        :return: Response
        """
        try:
            validate(request.json, Item.get_schema())
            item = Item()
            item.deserialize(request.json)

            db.session.add(item)
            db.session.commit()

        except ValidationError as e:
            db.session.rollback()
            return abort(400, e.message)

        except IntegrityError:
            db.session.rollback()
            return abort(409, "Item already exists")

        self._clear_cache()
        return Response(
            status=201, headers={"Location": url_for("api.itemitem", item=item)}
        )

    def _clear_cache(self):
        cache.delete(request.path)


class ItemItem(Resource):
    """
    Resource for a single item, provides PUT and DELETE methods
    /items/<item:item>/
    """

    @swag_from(os.getcwd() + f"{DOC_FOLDER}item/item/get.yml")
    @cache.cached(timeout=None, make_cache_key=request_path_cache_key)
    def get(self, item: Item) -> Response:
        """returns a single item

        :param item: item to return
        :return: Response
        """

        self_url = url_for("api.itemitem", item=item)
        body = InventoryManagerBuilder(item.serialize())

        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("profile", ITEM_PROFILE)
        body.add_control("collection", url_for("api.itemcollection"))
        body.add_control_put("Modify this item", self_url, Item.get_schema())
        body.add_control_delete("Delete this item", self_url)
        body.add_control_all_catalogue()
        body.add_control_all_stock()
        body.add_control_all_catalogue_item(item)
        body.add_control_all_stock_item(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}item/item/put.yml")
    def put(self, item: Item) -> Response:
        """Updates an item in the database

        :param item: Item to update
        :return: Response
        """
        try:
            validate(request.json, Item.get_schema())
            item.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            db.session.rollback()
            return create_error_response(400, "Invalid JSON document", str(e))

        except IntegrityError:
            db.session.rollback()
            return create_error_response(
                409,
                "Already exists",
                f"Item with name {request.json['name']} already exists.",
            )
        self._clear_cache()
        return Response(status=204)

    @swag_from(os.getcwd() + f"{DOC_FOLDER}item/item/delete.yml")
    def delete(self, item: Item) -> Response:
        """deletes an item from the database

        :param item: item to delete
        :return: Response
        """

        db.session.delete(item)
        db.session.commit()
        self._clear_cache()
        return Response(status=204)

    def _clear_cache(self):
        collection_path = url_for("api.itemcollection")
        cache.delete_many(collection_path, request.path)
