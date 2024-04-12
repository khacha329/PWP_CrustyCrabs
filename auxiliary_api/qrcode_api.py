"""
Auxiliary api that generates and reads qr codes to return information stock 
Structure copied from 
https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/auxiliary-api-example/
"""

import ast
import json
from io import BytesIO

import cv2
import numpy as np
import qrcode
import requests
from flask import Flask, Response, request
from flask_caching import Cache
from flask_restful import Api, Resource
from qreader import QReader
from werkzeug.exceptions import BadRequest, NotFound, ServiceUnavailable

# flask --app auxiliary_api/qrcode_api.py --debug run --port 5001
app = Flask(__name__)
app.config["INVENTORYMANAGER_API_SERVER"] = "http://localhost:5000"
app.config["INVENTORYMANAGER_API_TIMEOUT"] = 5
app.config["CACHE_TYPE"] = "FileSystemCache"
app.config["CACHE_DIR"] = "cache"

cache = Cache(app)
api = Api(app)

MASON = "application/vnd.mason+json"


#minmal version of version from
#https://github.com/enkwolf/pwp-course-sensorhub-api-example/tree/master
class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

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

        self["@namespaces"][ns] = {"name": uri}

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
    """calls the inventorymanager api with the given path and returns the response as a json object

    :param s: Session
    :param path: path to call
    :raises NotFound: If scanned QR Code information / pased json stock info can not be found
    :raises ServiceUnavailable: Raised if Inventorymanager not available
    :return: Response json
    """
    try:
        resp = s.get(
            app.config["INVENTORYMANAGER_API_SERVER"] + path,
            timeout=app.config["INVENTORYMANAGER_API_TIMEOUT"],
        )
        if resp.status_code == 404:
            raise NotFound("Invalid QR Code / Stock")

        return resp.json()

    except NotFound as e:
        raise e
    except Exception as e:
        raise ServiceUnavailable from e


@cache.memoize(120)
def get_stock(item_name: str, warehouse_id: int):
    """Get stock information from inventorymanager api

    :param item_name: item name of stock
    :param warehouse_id: warehouse_id of stock
    :return: Stock information
    """
    with requests.Session() as s:
        # s.headers.update({"Accept": "application/vnd.mason+json"})
        try:
            # hard to avoid hardcoding this
            stock = call_api(s, f"/api/stocks/{warehouse_id}/item/{item_name}/")

            stock_response_clean = {k: v for k, v in stock.items() if "@" not in k}
            return stock_response_clean

        except Exception as e:
            raise e


class QrGenerate(Resource):
    """
    Resource to generate a QR code for a given item name and warehouse id
    /api/qrGenerate/
    """

    def get(self):
        """Generates a QR code for a given item name and warehouse id
        Note: The item_name and warehouse_id are passed as query parameters

        :raises NotFound: Raised if stock is not found in inventorymanager api
        :raises ServiceUnavailable: Raised if inventorymanager api is not available
        :raises BadRequest: Raised if item_name or warehouse_id is missing
        :return: QR code image
        """
        try:
            item_name = request.args["item_name"]
            warehouse_id = request.args["warehouse_id"]
            stock_response = get_stock(item_name=item_name, warehouse_id=warehouse_id)
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
            img.save(payload, "PNG")
            payload.seek(0)

            return Response(payload, 200, mimetype="image/png")

        except NotFound as e:
            raise NotFound("Stock was not found / deleted from database") from e

        except ServiceUnavailable as e:
            raise ServiceUnavailable("Inventorymanager API Unavailable") from e

        except KeyError as e:
            raise BadRequest("Missing required fields") from e


class QrRead(Resource):
    """Reads a QR code image and returns the stock information
    /api/qrRead/
    """

    def get(self) -> Response:
        """Reads a QR code image and returns the stock information

        :raises BadRequest: Raised if encoded information in QR code is missing required fields
        :raises NotFound: Raised if stock is not found in inventorymanager api
        :raises ServiceUnavailable: Raised if inventorymanager api is not available
        :raises BadRequest: Raised if no image file provided under key 'image'
        :return: Stock information
        """

        try:
            image = request.files["image"]
            # Read the image file into memory
            image_bytes = image.read()
        except Exception as e:
            raise BadRequest("No image file provided under key 'image'") from e
        try:
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
            stock_response = get_stock(item_name=item_name, warehouse_id=warehouse_id)
            response_dict = decoded_dict.copy()
            response_dict["item_id"] = stock_response["item_id"]
            response_dict["Offline_quantity"] = response_dict.pop("quantity")
            response_dict["Offline_shelf_price"] = response_dict.pop("shelf_price")
            response_dict["Online_quantity"] = stock_response["quantity"]
            response_dict["Online_shelf_price"] = stock_response["shelf_price"]

            return Response(json.dumps(response_dict), 200, mimetype=MASON)

        except IndexError as e:
            raise BadRequest("No QR code detected") from e

        except NotFound as e:
            raise NotFound("Stock was not found / deleted from database") from e

        except ServiceUnavailable as e:
            raise ServiceUnavailable("Inventorymanager API Unavailable") from e

        except KeyError as e:
            raise BadRequest(
                "Encoded infromation in QR Code is missing required fields"
            ) from e


@app.route("/api/")
def entry():
    """Entrypoint for the api
    :return: Response with links to QrGenerate and QrRead
    """
    resp_data = MasonBuilder()
    resp_data.add_control("qrcode:generate", api.url_for(QrGenerate))
    resp_data.add_control("qrcode:read", api.url_for(QrRead))
    return Response(json.dumps(resp_data), 200, mimetype=MASON)


api.add_resource(QrGenerate, "/api/qrGenerate/")
api.add_resource(QrRead, "/api/qrRead/")
