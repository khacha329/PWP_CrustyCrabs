"""
Auxiliary api that generates and reads qr codes to return information stock 
Structure copied from https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/auxiliary-api-example/
"""

import json
import requests
from datetime import datetime
from flask import Flask, Response, request
from flask_caching import Cache
from flask_restful import Resource, Api
from werkzeug.exceptions import BadRequest, NotFound, ServiceUnavailable


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
            app.config["SENSORHUB_API_SERVER"] + path,
            timeout=app.config["SENSORHUB_API_TIMEOUT"],
        )
        return resp.json()
    except Exception as e:
        raise ServiceUnavailable

def follow_rel(s, doc, link_rel):
    try:
        path = doc["@controls"][link_rel]["href"]
    except KeyError:
        raise ServiceUnavailable
    else:
        data = call_api(s, path)
        return data

def get_sensors():
    with requests.Session() as s:
        s.headers.update({"Accept": "application/vnd.mason+json"})
        entry = call_api(s, "/api/")
        return follow_rel(s, entry, "senhub:sensors-all")

@cache.memoize(120)
def get_measurements(sensor, from_stamp, to_stamp):
    measurements = []
    with requests.Session() as s:
        s.headers.update({
            "Accept": "application/vnd.mason+json"
        })
        entry = call_api(s, "/api/")
        collection = follow_rel(s, entry, "senhub:sensors-all")
        for item in collection["items"]:
            if item["name"] == sensor:
                break
        else:
            raise NotFound
        
        sensor = follow_rel(s, item, "self")
        page = follow_rel(s, sensor, "senhub:measurements-first")
        while True:
            for item in page["items"]:
                stamp = datetime.fromisoformat(item["time"])
                if stamp > to_stamp:
                    return measurements
                elif stamp >= from_stamp:
                    measurements.append((item["time"], item["value"]))
            
            if "next" not in page["@controls"]:
                return measurements
            
            page = follow_rel(s, page, "next")
    

class QrScan(Resource):
    
    @cache.cached(timeout=10)
    def get(self):
        api_data = get_sensors()
        resp_data = MasonBuilder(
            items=[]
        )
        resp_data.add_namespace("measag", LINK_RELATIONS_URL)
        resp_data.add_control("self", api.url_for(SensorCollection))
        for sensor in api_data["items"]:
            item = MasonBuilder(
                name=sensor["name"],
                model=sensor["model"],
                location=sensor["location"],
            )
            item.add_control(
                "measag:measurements",
                api.url_for(MeasurementCollection,
                    sensor=sensor["name"]
                ) + "?from={from}&to={to}",
                kwargs={
                    "isHrefTemplate": True,
                    "schema": {
                        "properties": {
                            "from": {
                                "type": "string",
                                "format": "date-time",
                            },
                            "to": {
                                "type": "string",
                                "format": "date-time",
                            },
                        },
                        "required": ["from", "to"]
                    }
                }
            )
            resp_data["items"].append(item)
        return Response(json.dumps(resp_data), 200, mimetype=MASON)
        

class MeasurementCollection(Resource):

    def get(self, sensor):
        try:
            start = datetime.fromisoformat(request.args["from"])
            end = datetime.fromisoformat(request.args["to"])
        except (KeyError, ValueError):
            raise BadRequest
        
        resp_data = MasonBuilder()
        resp_data["items"] = get_measurements(
            sensor, start, end
        )
        resp_data.add_namespace("measag", LINK_RELATIONS_URL)
        resp_data.add_control("self", api.url_for(MeasurementCollection, sensor=sensor))
        resp_data.add_control(
            "measag:sensors-all",
            api.url_for(SensorCollection)
        )
        return Response(json.dumps(resp_data), 200, mimetype=MASON)
            

@app.route("/api/")
def entry():
    resp_data = MasonBuilder()
    resp_data.add_namespace("measag", LINK_RELATIONS_URL)
    resp_data.add_control(
        "measag:sensors-all",
        api.url_for(SensorCollection)
    )
    return Response(json.dumps(resp_data), 200, mimetype=MASON)
    
api.add_resource(SensorCollection, "/api/sensors/")
api.add_resource(MeasurementCollection, "/api/sensors/<sensor>/measurements/")



