"""
This module contains functionality related to testing the API
"""

import json
import os
import pytest
import tempfile
from flask.testing import FlaskClient
from jsonschema import validate
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError
from werkzeug.datastructures import Headers

from inventorymanager import create_app, db
from inventorymanager.models import Location, Warehouse, Item, Stock, Catalogue, create_dummy_data

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
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        _populate_db() #couldn't get create_dummy_data to work
        
    yield app.test_client()
    
    os.close(db_fd)
    os.unlink(db_fname)

def _populate_db():
    """
    Adds dummy data to the database
    """
    # Create dummy locations
    locations = [
        Location(latitude=60.1699, longitude=24.9384, country="Finland", postal_code="00100", city="Helsinki", street="Mannerheimintie"),
        Location(latitude=60.4518, longitude=22.2666, country="Finland", postal_code="20100", city="Turku", street="Aurakatu"),
    ]

    # Create dummy warehouses
    warehouses = [
        Warehouse(manager="John Doe", location=locations[0]),
        Warehouse(manager="Jane Doe", location=locations[1]),
    ]

    # Create dummy items
    items = [
        Item(name="Laptop-1", category="Electronics", weight=1.5),
        Item(name="Smartphone-1", category="Electronics", weight=0.2),
    ]

    # Create dummy stocks
    stocks = [
        Stock(item=items[0], warehouse=warehouses[0], quantity=10, shelf_price=999.99),
        Stock(item=items[1], warehouse=warehouses[1], quantity=20, shelf_price=599.99),
    ]

    # Create dummy catalogues
    catalogues = [
        Catalogue(item=items[0], supplier_name="TechSupplier A", min_order=5, order_price=950.00),
        Catalogue(item=items[1], supplier_name="TechSupplier B", min_order=10, order_price=550.00),
    ]

    # Add all to session and commit
    db.session.add_all(locations + warehouses + items + stocks + catalogues)
    db.session.commit()

def _get_item_json(number=2):
    """
    Creates a valid sensor JSON object to be used for PUT and POST tests.
    """
    return {'name': f'Laptop-{number}', 'category': 'Electronics', 'weight': 0.2}
    
# def _check_namespace(client, response):
#     """
#     Checks that the "senhub" namespace is found from the response body, and
#     that its "name" attribute is a URL that can be accessed.
#     """
    
#     ns_href = response["@namespaces"]["senhub"]["name"]
#     resp = client.get(ns_href)
#     assert resp.status_code == 200
    
# def _check_control_get_method(ctrl, client, obj):
#     """
#     Checks a GET type control from a JSON object be it root document or an item
#     in a collection. Also checks that the URL of the control can be accessed.
#     """
    
#     href = obj["@controls"][ctrl]["href"]
#     resp = client.get(href)
#     assert resp.status_code == 200
    
# def _check_control_delete_method(ctrl, client, obj):
#     """
#     Checks a DELETE type control from a JSON object be it root document or an
#     item in a collection. Checks the contrl's method in addition to its "href".
#     Also checks that using the control results in the correct status code of 204.
#     """
    
#     href = obj["@controls"][ctrl]["href"]
#     method = obj["@controls"][ctrl]["method"].lower()
#     assert method == "delete"
#     resp = client.delete(href)
#     assert resp.status_code == 204
    
# def _check_control_put_method(ctrl, client, obj):
#     """
#     Checks a PUT type control from a JSON object be it root document or an item
#     in a collection. In addition to checking the "href" attribute, also checks
#     that method, encoding and schema can be found from the control. Also
#     validates a valid sensor against the schema of the control to ensure that
#     they match. Finally checks that using the control results in the correct
#     status code of 204.
#     """
    
#     ctrl_obj = obj["@controls"][ctrl]
#     href = ctrl_obj["href"]
#     method = ctrl_obj["method"].lower()
#     encoding = ctrl_obj["encoding"].lower()
#     schema = ctrl_obj["schema"]
#     assert method == "put"
#     assert encoding == "json"
#     body = _get_sensor_json()
#     body["name"] = obj["name"]
#     validate(body, schema)
#     resp = client.put(href, json=body)
#     assert resp.status_code == 204
    
# def _check_control_post_method(ctrl, client, obj, obj_to_post): # currently not used
#     """
#     Checks a POST type control from a JSON object be it root document or an item
#     in a collection. In addition to checking the "href" attribute, also checks
#     that method, encoding and schema can be found from the control. Also
#     validates a valid sensor against the schema of the control to ensure that
#     they match. Finally checks that using the control results in the correct
#     status code of 201.
#     """
    
#     ctrl_obj = obj["@controls"][ctrl]
#     href = ctrl_obj["href"]
#     method = ctrl_obj["method"].lower()
#     encoding = ctrl_obj["encoding"].lower()
#     schema = ctrl_obj["schema"]
#     assert method == "post"
#     assert encoding == "json"
#     body = obj_to_post
#     validate(body, schema)
#     resp = client.post(href, json=body)
#     assert resp.status_code == 201


class TestItemCollection(object):
    
    RESOURCE_URL = "/api/items/"

    def test_get(self, client: FlaskClient):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body) == 2

        for item in body:

            assert "uri" in item
            resp = client.get(item["uri"]) 
            assert resp.status_code == 200

    def test_post(self, client: FlaskClient):
        valid = _get_item_json()
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["name"] + "/")
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
    
#     def test_get(self, client):
#         resp = client.get(self.RESOURCE_URL)
#         assert resp.status_code == 200
#         body = json.loads(resp.data)
#         _check_namespace(client, body)
#         _check_control_get_method("profile", client, body)
#         _check_control_get_method("collection", client, body)
#         _check_control_put_method("edit", client, body)
#         _check_control_delete_method("senhub:delete", client, body)
#         resp = client.get(self.INVALID_URL)
#         assert resp.status_code == 404

    def test_put(self, client: FlaskClient):
        valid = _get_item_json(number=1)
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data="notjson", headers=Headers({"Content-Type": "text"}))
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
        with pytest.raises(AssertionError):
            resp = client.delete(self.RESOURCE_URL)
        db.session.rollback()
        # delete the stock 
        db.session.delete(Stock.query.filter_by(item_id=1).first())
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204

        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
        
        
if __name__ == "__main__":
    client()      
        
        
        
        
        
        
        
        
    
    

    

        
            
    