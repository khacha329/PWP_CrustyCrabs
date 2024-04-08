"""
Auxiliary api that generates and reads qr codes to return information stock 
Structure copied from https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/auxiliary-api-example/
"""

import json
import requests
from datetime import datetime
import numpy as np
import qrcode
from io import BytesIO
from flask import Flask, Response, request
from flask_caching import Cache
from flask_restful import Resource, Api
from werkzeug.exceptions import BadRequest, NotFound, ServiceUnavailable
from qreader import QReader
import cv2
import ast


#flask --app auxiliary_api/qrcode_api.py --debug run --port 5001
app = Flask(__name__)
app.config["INVENTORYMANAGER_API_SERVER"] = "http://localhost:5000"
app.config["INVENTORYMANAGER_API_TIMEOUT"] = 5
app.config["CACHE_TYPE"] = "FileSystemCache"
app.config["CACHE_DIR"] = "cache"

cache = Cache(app)
api = Api(app)

MASON = "application/vnd.mason+json"
LINK_RELATIONS_URL = "/qrcode/link-relations/"

class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href


def call_api(s, path):
    try:
        resp = s.get(
            app.config["INVENTORYMANAGER_API_SERVER"] + path,
            timeout=app.config["INVENTORYMANAGER_API_TIMEOUT"],
        )
        return resp.json()
    except Exception as e:
        raise ServiceUnavailable

@cache.memoize(120)
def get_stock(item_name : str, warehouse_id : int):
    with requests.Session() as s:
        #s.headers.update({"Accept": "application/vnd.mason+json"})
        try: 
            #hard to avoid hardcoding this
            stock = call_api(s, f"/api/stocks/{warehouse_id}/item/{item_name}/")

            stock_response_clean = {k: v for k, v in stock.items() if "@" not in k}
            return stock_response_clean

        except Exception as e:
            print(e)
        

class qrGenerate(Resource):
    
    def get(self):
        item_name = request.args["item_name"]
        warehouse_id = request.args["warehouse_id"]
        stock_response = get_stock(item_name = item_name, warehouse_id = warehouse_id)
        stock_response["item_name"] = item_name

        qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
        )   
        qr.add_data(stock_response)
        img = qr.make_image(fill_color="black", back_color="white")


        payload = BytesIO()
        img.save(payload, 'PNG')
        payload.seek(0)

        return Response(payload, 200, mimetype='image/png')
        

class qrRead(Resource):

    def get(self):
        image = request.files["image"]

        # Read the image file into memory
        image_bytes = image.read()

        # Create a QReader instance
        qreader = QReader()

        # Convert the image to OpenCV format
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), -1)

        # Use the detect_and_decode function to get the decoded QR data
        decoded_text = qreader.detect_and_decode(image=image)[0]
        decoded_dict = ast.literal_eval(decoded_text)

        item_name = decoded_dict["item_name"]
        warehouse_id = decoded_dict["warehouse_id"]
        print(item_name)
        print(warehouse_id)
        stock_response = get_stock(item_name = item_name, warehouse_id = warehouse_id)
        response_dict = decoded_dict.copy()
        response_dict["item_id"] = stock_response["item_id"]
        response_dict["Offline_quantity"] = response_dict.pop("quantity")
        response_dict["Offline_shelf_price"] = response_dict.pop("shelf_price")
        response_dict["Online_quantity"] = stock_response["quantity"]
        response_dict["Online_shelf_price"] = stock_response["shelf_price"]
        return response_dict
        
@app.route("/api/")
def entry():
    resp_data = MasonBuilder()
    #resp_data.add_namespace("qrcode", LINK_RELATIONS_URL)
    resp_data.add_control(
        "qrcode:generate",
        api.url_for(qrGenerate)
    )
    resp_data.add_control(
        "qrcode:read",
        api.url_for(qrRead)
    )
    return Response(json.dumps(resp_data), 200, mimetype=MASON)
    
api.add_resource(qrGenerate, "/api/qrGenerate/")
api.add_resource(qrRead, "/api/qrRead/")



