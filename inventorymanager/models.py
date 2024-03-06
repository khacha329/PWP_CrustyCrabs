"""
This module contains all Model classes for our API, as well as click functions callable
    from the command line
The classes are:
 - Location
 - Warehouse
 - Item
 - Stock
 - Catalogue
The functions are responsible for initiliazing and populating the database
"""

import click
from flask.cli import with_appcontext
from sqlalchemy import CheckConstraint, event, text
from sqlalchemy.engine import Engine

from inventorymanager import db


# from the Exercise 1 webpage
# https://lovelace.oulu.fi/ohjelmoitava-web/ohjelmoitava-web/introduction-to-web-development/#sidenote-foreign-keys-in-sqlite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Called when a connection to the database is established.
    Activates the constraints on foreign keys.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Location model
class Location(db.Model):
    """Location class for the database."""

    location_id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    country = db.Column(db.String(64), nullable=False, default="Finland")
    postal_code = db.Column(db.String(8), nullable=False)
    city = db.Column(db.String(64), nullable=False)
    street = db.Column(db.String(64), nullable=False)

    warehouse = db.relationship(
        "Warehouse", back_populates="location", uselist=False
    )  # can't be deleted if warehouse exists with location?

    __table_args__ = (
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90", name="latitude_constraint"
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180", name="longitude_constraint"
        ),
    )

    @staticmethod
    def get_schema() -> dict:
        """schema for the Location model

        :return: location schema
        """
        return {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
                "country": {"type": "string"},
                "postal_code": {"type": "string"},
                "city": {"type": "string"},
                "street": {"type": "string"},
            },
            "required": ["country", "postal_code", "city", "street"],
            "additionalProperties": False,
        }

    def serialize(self) -> dict:
        """Converts location to dictionary

        :return: warehouse dictionary
        """
        return {
            "location_id": self.location_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country": self.country,
            "postal_code": self.postal_code,
            "city": self.city,
            "street": self.street,
        }

    def deserialize(self, doc: dict) -> None:
        """converts dict to location object

        :param doc: dictionary with location information
        """
        self.latitude = doc.get("latitude", self.latitude)
        self.longitude = doc.get("longitude", self.longitude)
        self.country = doc.get("country", self.country)
        self.postal_code = doc.get("postal_code", self.postal_code)
        self.city = doc.get("city", self.city)
        self.street = doc.get("street", self.street)

    def __repr__(self):
        return (
            f"<Location {self.location_id}, {self.city}, {self.country}, "
            f"Latitude: {self.latitude}, Longitude: {self.longitude}, "
            f"Postal Code: {self.postal_code}, Street: {self.street}>"
        )


# Warehouse model
class Warehouse(db.Model):
    """Warehouse class for the database."""

    warehouse_id = db.Column(db.Integer, primary_key=True)
    manager = db.Column(db.String(64), nullable=True)
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("location.location_id", ondelete="RESTRICT"),
        nullable=False,
    )

    location = db.relationship("Location", back_populates="warehouse", uselist=False)
    stock = db.relationship(
        "Stock", back_populates="warehouse", cascade="all, delete-orphan", uselist=True
    )

    __table_args__ = (
        CheckConstraint(text("manager LIKE '% %'"), name="manager_constraint"),
    )

    @staticmethod
    def get_schema() -> dict:
        """schema for the Warehouse model

        :return: warehouse schema
        """

        return {
            "type": "object",
            "properties": {
                "manager": {"type": "string"},
                "location_id": {"type": "integer"},
            },
            "required": [],
            "additionalProperties": False,
        }

    def serialize(self) -> dict:
        """converts warehouse to dictionary"""
        return {
            "warehouse_id": self.warehouse_id,
            "manager": self.manager,
            "location_id": self.location_id,
        }

    def deserialize(self, doc: dict):
        """converts dict to warehouse object

        :param doc: dictionary with warehouse information
        """
        self.manager = doc.get("manager", self.manager)
        self.location_id = doc.get("location_id", self.location_id)

    def __repr__(self):
        return f"<Warehouse(id={self.warehouse_id}, manager='{self.manager}', location_id={self.location_id})>"


# Item model
class Item(db.Model):
    """Item class for the database."""

    item_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    category = db.Column(db.String(64), nullable=True)
    weight = db.Column(db.Float, nullable=True)

    stock = db.relationship(
        "Stock", back_populates="item", uselist=True
    )  # don't cascade so that it throws an error if stock exists with item when deleted
    catalogue = db.relationship(
        "Catalogue", back_populates="item", cascade="all, delete-orphan", uselist=True
    )

    __table_args__ = (CheckConstraint("weight >= 0", name="weight_constraint"),)

    @staticmethod
    def get_schema() -> dict:
        """schema for the Item model

        :return: item schema
        """
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "category": {"type": "string"},
                "weight": {"type": "number"},
            },
            "required": ["name"],
            "additionalProperties": False,
        }

    def serialize(self) -> dict:
        """converts item to dictionary

        :return: item dictionary
        """
        return {
            "item_id": self.item_id,
            "name": self.name,
            "category": self.category,
            "weight": self.weight,
        }

    def deserialize(self, doc: dict) -> None:
        """converts dict to item object

        :param doc: dictionary with item information
        """
        self.name = doc.get("name", self.name)
        self.category = doc.get("category", self.category)
        self.weight = doc.get("weight", self.weight)

    def __repr__(self):
        return f"<Item(id={self.item_id}, name='{self.name}', category='{self.category}', weight={self.weight})>"


# Stock model
class Stock(db.Model):
    """Stock class for the database."""

    item_id = db.Column(
        db.Integer, db.ForeignKey("item.item_id", ondelete="RESTRICT"), primary_key=True
    )
    warehouse_id = db.Column(
        db.Integer,
        db.ForeignKey("warehouse.warehouse_id", ondelete="CASCADE"),
        primary_key=True,
    )
    # quantity should be >= 0
    quantity = db.Column(db.Integer, nullable=False)
    shelf_price = db.Column(db.Float, nullable=True)

    item = db.relationship("Item", back_populates="stock", uselist=False)
    warehouse = db.relationship("Warehouse", back_populates="stock", uselist=False)

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="quantity_constraint"),
        CheckConstraint("shelf_price >= 0", name="shelf_price_constraint"),
    )

    @staticmethod
    def get_schema() -> dict:
        """schema for the Stock model

        :return: stock schema
        """
        return {
            "type": "object",
            "properties": {
                "item_name": {"type":"string"},
                "warehouse_id": {"type":"int"},
                "quantity": {"type": "integer"},
                "shelf_price": {"type": "number"},
            },
            "required": ["quantity"],
            "additionalProperties": False,
        }

    def serialize(self) -> dict:
        """converts stock to dictionary

        :return: stock dictionary
        """
        return {
            "item_id": self.item_id,
            "warehouse_id": self.warehouse_id,
            "quantity": self.quantity,
            "shelf_price": self.shelf_price,
        }

    def deserialize(self, doc: dict) -> None:
        """converts dict to stock object

        :param doc: dictionary with stock information
        """
        self.quantity = doc.get("quantity", self.quantity)
        self.shelf_price = doc.get("shelf_price", self.shelf_price)

    def __repr__(self):
        return f"<Stock(item_id={self.item_id}, warehouse_id={self.warehouse_id}, quantity={self.quantity}, shelf_price={self.shelf_price})>"


# Catalogue model
class Catalogue(db.Model):
    """Catalogue class for the database."""

    item_id = db.Column(
        db.Integer, db.ForeignKey("item.item_id", ondelete="CASCADE"), primary_key=True
    )
    supplier_name = db.Column(db.String(64), primary_key=True)
    min_order = db.Column(db.Integer, nullable=False)
    order_price = db.Column(db.Float, nullable=True)

    item = db.relationship("Item", back_populates="catalogue", uselist=False)

    __table_args__ = (CheckConstraint("min_order >= 1", name="min_order_constraint"),)

    @staticmethod
    def get_schema() -> dict:
        """schema for the Catalogue model

        :return: catalogue schema
        """
        return {
            "type": "object",
            "properties": {
                "item_name": {"type":"string"},
                "supplier_name": {"type": "string"},
                "min_order": {"type": "integer"},
                "order_price": {"type": "number"},
            },
            "required": ["supplier_name", "min_order"],
            "additionalProperties": False,
        }

    def serialize(self) -> dict:
        """Converts catalogue to dictionary

        :return: catalogue dictionary
        """
        return {
            "item_id": self.item_id,
            "supplier_name": self.supplier_name,
            "min_order": self.min_order,
            "order_price": self.order_price,
        }

    def deserialize(self, doc: dict) -> None:
        """Converts dict to catalogue object

        :param doc: dictionary with catalogue information
        """
        self.supplier_name = doc.get("supplier_name", self.supplier_name)
        self.min_order = doc.get("min_order", self.min_order)
        self.order_price = doc.get("order_price", self.order_price)

    def __repr__(self):
        return f"<Catalogue(item_id={self.item_id}, supplier_name='{self.supplier_name}', min_order={self.min_order}, order_price={self.order_price})>"


@click.command("init-db")
@with_appcontext
def init_db_command() -> None:
    """
    Initializes the database
    """
    db.create_all()


@click.command("populate-db")
@with_appcontext
def create_dummy_data() -> None:
    """
    Adds dummy data to the database
    """
    # Create dummy locations
    locations = [
        Location(
            latitude=60.1699,
            longitude=24.9384,
            country="Finland",
            postal_code="00100",
            city="Helsinki",
            street="Mannerheimintie",
        ),
        Location(
            latitude=60.4518,
            longitude=22.2666,
            country="Finland",
            postal_code="20100",
            city="Turku",
            street="Aurakatu",
        ),
    ]

    # Create dummy warehouses
    warehouses = [
        Warehouse(manager="John Doe", location=locations[0]),
        Warehouse(manager="Jane Doe", location=locations[1]),
    ]

    # Create dummy items
    items = [
        Item(name="Laptop", category="Electronics", weight=1.5),
        Item(name="Smartphone", category="Electronics", weight=0.2),
    ]

    # Create dummy stocks
    stocks = [
        Stock(item=items[0], warehouse=warehouses[0], quantity=10, shelf_price=999.99),
        Stock(item=items[1], warehouse=warehouses[1], quantity=20, shelf_price=599.99),
       # Stock(item=items[0], warehouse=warehouses[1], quantity=30, shelf_price=899.99),
    ]

    # Create dummy catalogues
    catalogues = [
        Catalogue(
            item=items[0],
            supplier_name="TechSupplier A",
            min_order=5,
            order_price=950.00,
        ),
        Catalogue(
            item=items[1],
            supplier_name="TechSupplier B",
            min_order=10,
            order_price=550.00,
        ),
        # Catalogue(
        #     item=items[0],
        #     supplier_name="TechSupplier B",
        #     min_order=15,
        #     order_price=850.00,
        # ),
    ]

    # Add all to session and commit
    db.session.add_all(locations + warehouses + items + stocks + catalogues)
    db.session.commit()


if __name__ == "__main__":
    test_location = Location(
        location_id=5,
        latitude=60.1699,
        longitude=24.9384,
        country="Finland",
        postal_code="00100",
        city="Helsinki",
        street="Mannerheimintie",
    )
    print(test_location.serialize())
    test_location_json = {
        "latitude": 69,
        "longitude": 42,
        "country": "Finland",
        "postal_code": "00100",
        "city": "Helsinki",
        "street": "Mannerheimintie",
    }
    test_location.deserialize(test_location_json)
    print(test_location)

    test_warehouse = Warehouse(manager="John Doe", location=test_location)
    print(test_warehouse.serialize())
    test_warehouse_json = {"manager": "Jane Doe", "location_id": 5}
    test_warehouse.deserialize(test_warehouse_json)
    print(test_warehouse)

    test_item = Item(name="Laptop", category="Electronics", weight=1.5)
    print(test_item.serialize())
    test_item_json = {"name": "Smartphone", "category": "Electronics", "weight": 0.2}
    test_item.deserialize(test_item_json)
    print(test_item)

    test_stock = Stock(
        item=test_item, warehouse=test_warehouse, quantity=10, shelf_price=999.99
    )
    print(test_stock.serialize())
    test_stock_json = {"quantity": 20, "shelf_price": 599.99}
    test_stock.deserialize(test_stock_json)
    print(test_stock)

    test_catalogue = Catalogue(
        item=test_item, supplier_name="TechSupplier A", min_order=5, order_price=950.00
    )
    print(test_catalogue.serialize())
    test_catalogue_json = {
        "supplier_name": "TechSupplier B",
        "min_order": 10,
        "order_price": 550.00,
    }
    test_catalogue.deserialize(test_catalogue_json)
    print(test_catalogue)

    from jsonschema import validate

    validate(test_location_json, Location.get_schema())
    validate(test_warehouse_json, Warehouse.get_schema())
    validate(test_item_json, Item.get_schema())
    validate(test_stock_json, Stock.get_schema())
    validate(test_catalogue_json, Catalogue.get_schema())
