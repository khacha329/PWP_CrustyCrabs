""" Item resource module """

import json

from flask import Response, abort, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from sqlalchemy.exc import IntegrityError

from inventorymanager import db
from inventorymanager.models import Item
from inventorymanager.utils import create_error_response
from inventorymanager.constants import (
    MASON,
    LINK_RELATIONS_URL,
    NAMESPACE,
    INVENTORY_PROFILE,
)
from inventorymanager.builder import InventoryManagerBuilder


class ItemCollection(Resource):
    """
    Resource for the collection of items, provides GET and POST methods
    """

    def get(self) -> Response:
        """Returns a list of all items in the database

        :return: Response
        """
        body = []
        for item in Item.query.all():
            item_json = item.serialize()
            item_json["uri"] = url_for("api.itemitem", item=item)
            body.append(item_json)

        return Response(json.dumps(body), 200)

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
            return abort(400, e.message)

        except IntegrityError:
            return abort(409, "Item already exists")

        return Response(
            status=201, headers={"Location": url_for("api.itemitem", item=item)}
        )


class ItemItem(Resource):
    """
    Resource for a single item, provides PUT and DELETE methods
    """

    def get(self, item: Item) -> None:
        """placeholder

        :param item: placeholders
        """
        if not item:
            return create_error_response(404, "Item doesn't exist")

        self_url = url_for("api.itemitem", item=item)
        body = InventoryManagerBuilder(item.serialize())

        body.add_namespace(NAMESPACE, LINK_RELATIONS_URL)
        body.add_control("self", self_url)
        body.add_control("profile", INVENTORY_PROFILE)
        body.add_control("collection", url_for("api.itemcollection"))
        body.add_control_put("Modify this item", self_url, Item.get_schema())
        body.add_control_delete("Delete this item", self_url)
        body.add_control_all_catalogue()
        body.add_control_all_stock()

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, item: Item) -> Response:
        """Updates an item in the database

        :param item: Item to update
        :return: Response
        """
        if not item:
            return create_error_response(404, "Item doesn't exist")
        try:
            validate(request.json, Item.get_schema())
            item.deserialize(request.json)
            db.session.commit()

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        except IntegrityError:
            return create_error_response(
                409,
                "Already exists",
                f"Item with name {request.json['name']} already exists.",
            )

        return Response(status=204)

    def delete(self, item: Item) -> Response:
        """deletes an item from the database

        :param item: item to delete
        :return: Response
        """
        if not item:
            return create_error_response(404, "Item doesn't exist")
        db.session.delete(item)
        db.session.commit()

        return Response(status=204)
