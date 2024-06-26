"""
This module contains functionality related to testing the API
"""

import json
import os
import pytest
import tempfile
from flask.testing import FlaskClient
from jsonschema import ValidationError, validate
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError
from werkzeug.datastructures import Headers


from inventorymanager import create_app, db
from inventorymanager.models import (
    Location,
    Warehouse,
    Item,
    Stock,
    Catalogue,
    populate_db,
)

from inventorymanager.constants import (
    ITEM_PROFILE,
    WAREHOUSE_PROFILE,
    CATALOGUE_PROFILE,
    STOCK_PROFILE,
    LOCATION_PROFILE,
    LINK_RELATIONS_URL,
    MASON,
    NAMESPACE,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    config = {"SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname, "TESTING": True}

    app = create_app(config)

    # with app.app_context():
    db.create_all()

    populate_db()

    # _populate_db()  # couldn't get create_dummy_data to work

    yield app.test_client()

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)


def _get_item_json(number=2):
    """
    Creates a valid item JSON object to be used for PUT and POST tests.
    """
    return {"name": f"Laptop-{number}", "category": "Electronics", "weight": 0.2}


def _get_warehouse_json(number):
    """
    Creates a valid warehouse JSON object to be used for PUT and POST tests.
    """
    return {"warehouse_id": number, "manager": "John Elmeri", "location_id": 1}


def _get_location_json(number):
    """
    Creates a valid location JSON object to be used for PUT and POST tests.
    """
    return {
        "location_id": number,
        "latitude": 70,
        "longitude": 50,
        "country": "Finland",
        "postal_code": "90570",
        "city": "oulu",
        "street": "yliopistokatu 24",
    }


def _get_stock_json(item_id, warehouse_id):
    """
    Creates a valid stock JSON object to be used for PUT and POST tests.
    """
    return {
        "item_id": item_id,
        "warehouse_id": warehouse_id,
        "quantity": 20,
        "shelf_price": 750.00,
    }


def _get_catalogue_json(number):
    """
    Creates a valid catalogue JSON object to be used for PUT and POST tests.
    """
    return {
        "item_id": number,
        "supplier_name": "TechSupplier A",
        "min_order": 30,
        "order_price": 600.00,
    }


# from https://github.com/enkwolf/pwp-course-sensorhub-api-example/blob/master/tests/resource_test.py
def _check_namespace(client, response):
    """
    Checks that the "senhub" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """

    ns_href = response["@namespaces"][NAMESPACE]["name"]
    resp = client.get(ns_href)
    assert resp.status_code == 200


def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 200


def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204


def _check_control_put_method(ctrl, client, obj, obj_json, identifier):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    body = obj_json
    body[identifier] = obj[identifier]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204


def _check_control_post_method(ctrl, client, obj, obj_json):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = obj_json
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201


class TestEntryPoint(object):
    RESOURCE_URL = "/api/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method(f"{NAMESPACE}:warehouses-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:items-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:stock-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:catalogues-all", client, body)


class TestLocationCollection(object):
    RESOURCE_URL = "/api/locations/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200

        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method(
            f"{NAMESPACE}:add-location", client, body, _get_location_json(97)
        )
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:warehouses-all", client, body)
        
        assert len(body["locations"]) == 2
        for item in body["locations"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_post(self, client: FlaskClient):
        valid = _get_location_json(3)

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(
            self.RESOURCE_URL + str(valid["location_id"]) + "/"
        )
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # remove model field for 400
        valid.pop("country")
        with pytest.raises(ValidationError):
            validate(valid, Location.get_schema())
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestLocationItem(object):

    RESOURCE_URL = "/api/locations/1/"
    INVALID_URL = "/api/locations/Tokmani/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("profile", client, body)
        # _check_control_put_method("edit", client, body, _get_location_json(4), "city")
        _check_control_get_method("collection", client, body)

        _check_control_delete_method(f"{NAMESPACE}:delete", client, body)
        
        # assert len(body) == 9

        # assert "uri" in body
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client: FlaskClient):
        valid = _get_location_json(1)

        # test with wrong content type
        resp = client.put(
            self.RESOURCE_URL, data="notjson", headers=Headers({"Content-Type": "text"})
        )
        assert resp.status_code in (400, 415)

        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

        # test with another warehouse id
        valid["location_id"] = 2
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        db.session.rollback()

        # test with valid (only change model)
        valid["location_id"] = 1
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        # remove model field for 400
        valid.pop("country")
        with pytest.raises(ValidationError):
            validate(valid, Location.get_schema())
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_delete(self, client: FlaskClient):

        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204

        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestItemCollection(object):

    RESOURCE_URL = "/api/items/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method(
            f"{NAMESPACE}:add-item", client, body, _get_item_json()
        )
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:stock-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:catalogues-all", client, body)

        assert len(body["items"]) == 3
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_post(self, client: FlaskClient):
        valid = _get_item_json()

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(
            self.RESOURCE_URL + valid["name"] + "/"
        )
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # remove model field for 400
        valid.pop("name")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestItemItem(object):

    RESOURCE_URL = "/api/items/Laptop-1/"
    INVALID_URL = "/api/items/NotAnItem/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("profile", client, body)
        _check_control_put_method("edit", client, body, _get_item_json(), "name")

        _check_control_get_method("collection", client, body)
        _check_control_get_method(f"{NAMESPACE}:catalogues-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:stock-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:catalogue-item-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:stock-item-all", client, body)

        _check_control_delete_method(f"{NAMESPACE}:delete", client, body)

        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client: FlaskClient):
        valid = _get_item_json(number=2)

        # test with wrong content type
        resp = client.put(
            self.RESOURCE_URL, data="notjson", headers=Headers({"Content-Type": "text"})
        )
        assert resp.status_code in (400, 415)

        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

        # test with another sensor's name
        valid["name"] = "Smartphone-1"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        db.session.rollback()

        # test with valid (only change model)
        valid["name"] = "Laptop-1"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # remove field for 400
        valid.pop("name")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_delete(self, client: FlaskClient):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestWarehouseCollection(object):

    RESOURCE_URL = "/api/warehouses/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200

        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method(
            f"{NAMESPACE}:add-warehouse", client, body, _get_warehouse_json(4)
        )
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:locations-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:items-all", client, body)

        # warehouses = Warehouse.query.all()
        assert len(body["warehouses"]) == 2

        for warehouse in body["warehouses"]:
            _check_control_get_method("self", client, warehouse)
            _check_control_get_method("profile", client, warehouse)
            # assert resp.status_code == 200

    def test_post(self, client: FlaskClient):
        valid = _get_warehouse_json(4)

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(
            self.RESOURCE_URL + str(valid["warehouse_id"]) + "/"
        )
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409


class TestWarehouseItem(object):

    RESOURCE_URL = "/api/warehouses/1/"
    INVALID_URL = "/api/warehouses/Tokmani/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200

        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("profile", client, body)
        _check_control_put_method(
            "edit", client, body, _get_warehouse_json(1), "manager"
        )
        _check_control_get_method(f"{NAMESPACE}:stock-warehouse-all", client, body)
        _check_control_delete_method(f"{NAMESPACE}:delete", client, body)
        
        
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client: FlaskClient):
        valid = _get_warehouse_json(3)

        # test with wrong content type
        resp = client.put(
            self.RESOURCE_URL, data="notjson", headers=Headers({"Content-Type": "text"})
        )
        assert resp.status_code in (400, 415)

        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404

        # test with another warehouse id
        valid["warehouse_id"] = 2
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        db.session.rollback()

        # test with valid (only change model)
        valid["warehouse_id"] = 1
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

    def test_delete(self, client: FlaskClient):

        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204

        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestCatalogueCollection(object):

    RESOURCE_URL = "/api/catalogue/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        _check_namespace(client, body)
        _check_control_post_method(
            f"{NAMESPACE}:add-catalogue", client, body, _get_catalogue_json(2)
        )
        # import pdb; pdb.set_trace()
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:items-all", client, body)

        # catalogues = Catalogue.query.all()
        # assert len(body["catalogues"]) == len(catalogues)

        for catalogue in body["catalogues"]:
            _check_control_get_method("self", client, catalogue)
            _check_control_get_method("profile", client, catalogue)

    def test_post(self, client: FlaskClient):
        valid = _get_catalogue_json(2)

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        # to extract item name
        item_entry = Item.query.filter_by(item_id=valid["item_id"]).first()
        # account for spullier name with spaces
        valid["supplier_name"] = valid["supplier_name"].replace(" ", "%20")
        assert resp.headers["Location"].endswith(
            self.RESOURCE_URL
            + "supplier/"
            + valid["supplier_name"]
            + "/item/"
            + item_entry.name
            + "/"
        )  # issue with name having spaces and item id being the id instead of item name
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        # replace supplier name back to having spaces
        valid["supplier_name"] = valid["supplier_name"].replace("%20", " ")
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        valid = _get_catalogue_json(4)
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        valid.pop("supplier_name")
        with pytest.raises(ValidationError):
            validate(valid, Catalogue.get_schema())
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestCatalogueItem(object):

    RESOURCE_URL = "/api/catalogue/supplier/TechSupplier%20A/item/Laptop-1/"
    INVALID_URL = "/api/catalogue/supplier/Apple/item/Chair/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method(
            "edit", client, body, _get_catalogue_json(1), "supplier_name"
        )
        _check_control_get_method(f"{NAMESPACE}:item", client, body)
        _check_control_get_method(f"{NAMESPACE}:catalogue-supplier-all", client, body)

        _check_control_delete_method(f"{NAMESPACE}:delete", client, body)
        # assert len(body) == 5

        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client: FlaskClient):
        valid = _get_catalogue_json(2)

        # test with wrong content type
        resp = client.put(
            self.RESOURCE_URL, data="notjson", headers=Headers({"Content-Type": "text"})
        )
        assert resp.status_code in (400, 415)

        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        # test for non existing item
        valid["item_id"] = 7
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        # test with another catalogue id (item id + supplier name)
        valid["item_id"] = 2
        valid["supplier_name"] = "TechSupplier B"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        db.session.rollback()

        # test with valid (only change model)
        valid["item_id"] = 1
        valid["supplier_name"] = "TechSupplier A"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        valid.pop("supplier_name")
        with pytest.raises(ValidationError):
            validate(valid, Catalogue.get_schema())
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_delete(self, client: FlaskClient):

        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204

        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestCatalogueItemCollection(object):
    RESOURCE_URL = "/api/catalogue/item/Laptop-1/"
    NOITEM_URL = "/api/catalogue/item/Laptop-2/"
    OUTOFSTOCK_URL = "/api/catalogue/item/Laptop-3/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:catalogues-all", client, body)
        
        assert len(body["catalogues"]) == 1

        for catalogue in body["catalogues"]:
            _check_control_get_method("self", client, catalogue)
            _check_control_get_method("profile", client, catalogue)
        
        resp = client.get(self.NOITEM_URL)
        assert resp.status_code == 404
        resp = client.get(self.OUTOFSTOCK_URL)
        assert resp.status_code == 404


class TestCatalogueSupplierCollection(object):
    RESOURCE_URL = "/api/catalogue/supplier/TechSupplier%20A/"
    NOSUPPLIER_URL = "/api/catalogue/supplier/TechSupplier%20C/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:catalogues-all", client, body)
        assert len(body["catalogues"]) == 1

        for catalogue in body["catalogues"]:
            _check_control_get_method("self", client, catalogue)
            _check_control_get_method("profile", client, catalogue)
            resp = client.get(self.NOSUPPLIER_URL)
            assert resp.status_code == 404


class TestStockCollection(object):

    RESOURCE_URL = "/api/stocks/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method(
            f"{NAMESPACE}:add-stock", client, body, _get_stock_json(2, 1)
        )
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:items-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:warehouses-all", client, body)

        assert len(body["items"]) == 2
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_post(self, client: FlaskClient):
        valid = _get_stock_json(1, 2)

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        # to extract item name
        item_entry = Item.query.filter_by(item_id=valid["item_id"]).first()

        assert resp.headers["Location"].endswith(
            self.RESOURCE_URL
            + str(valid["warehouse_id"])
            + "/item/"
            + item_entry.name
            + "/"
        )  # issue with name having spaces and item id being the id instead of item name
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        valid = _get_stock_json(4, 2)
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        valid = _get_stock_json(1, 3)
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        valid = _get_stock_json(1, 2)
        valid.pop("quantity")
        with pytest.raises(ValidationError):
            validate(valid, Stock.get_schema())
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestStockItem(object):

    RESOURCE_URL = "/api/stocks/1/item/Laptop-1/"
    INVALID_URL = "/api/stocks/2/item/Chair/"
    INVALID_ITEM = "/api/stocks/1/item/Laptop-2/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("profile", client, body)
        _check_control_put_method(
            "edit", client, body, _get_stock_json(1, 1), "item_id"
        )  # should be combinaton of warehouse_id and stock_id in theory

        _check_control_get_method("collection", client, body)
        _check_control_get_method(f"{NAMESPACE}:item", client, body)
        _check_control_get_method(f"{NAMESPACE}:warehouse", client, body)
        _check_control_get_method(f"{NAMESPACE}:stock-warehouse-all", client, body)
        _check_control_get_method(f"{NAMESPACE}:stock-item-all", client, body)

        _check_control_delete_method(f"{NAMESPACE}:delete", client, body)

        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client: FlaskClient):
        valid = _get_stock_json(2, 2)

        # test with wrong content type
        resp = client.put(
            self.RESOURCE_URL, data="notjson", headers=Headers({"Content-Type": "text"})
        )
        assert resp.status_code in (400, 415)

        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        resp = client.put(self.INVALID_ITEM, json=valid)
        assert resp.status_code == 404
        # test for non existing item or warehouse
        valid["item_id"] = 7
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        valid["item_id"] = 2
        valid["warehouse_id"] = 7
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        # test with another warehouse id (item id + warehouse id)
        valid = _get_stock_json(2, 2)
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        db.session.rollback()

        # test with valid (only change model)
        valid = _get_stock_json(1, 2)
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        valid = _get_stock_json(2, 2)
        valid.pop("quantity")
        with pytest.raises(ValidationError):
            validate(valid, Stock.get_schema())
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

    def test_delete(self, client: FlaskClient):

        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204

        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestStockItemCollection(object):
    RESOURCE_URL = "/api/stocks/item/Laptop-1/"
    NOITEM_URL = "/api/stocks/item/Laptop-69/"

    def test_get(self, client: FlaskClient):

        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:stock-all", client, body)

        assert len(body["items"]) == 1
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

        resp = client.get(self.NOITEM_URL)
        assert resp.status_code == 404


class TestStockWarehouseCollection(object):
    RESOURCE_URL = "/api/stocks/warehouse/1/"
    NOWAREHOUSE_URL = "/api/stocks/warehouse/4/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method(f"{NAMESPACE}:stock-all", client, body)

        assert len(body["items"]) == 1
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

        resp = client.get(self.NOWAREHOUSE_URL)
        assert resp.status_code == 404
