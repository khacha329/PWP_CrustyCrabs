"""this class provides builder helper functions for hypermedia controls and
    error messages. It is used to create Mason objects that are returned as
    responses to the client. 
"""

from flask import url_for

from inventorymanager.constants import NAMESPACE
from inventorymanager.models import Item, Warehouse


# from https://github.com/enkwolf/pwp-course-sensorhub-api-example/tree/master
class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title: str, details: str) -> None:
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        :param title: Short title for the error
        :param details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns: str, uri: str) -> None:
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        :param ns: the namespace prefix
        :param uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {"name": uri}

    def add_control(self, ctrl_name: str, href: str, **kwargs) -> None:
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        :param ctrl_name: name of the control (including namespace if any)
        :param href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

    # https://github.com/lorenzo-medici/PWP_StudentManager/blob/main/studentmanager/builder.py#L150
    def add_control_post(self, ctrl_name, title, href, schema):
        """
        Utility method for adding POST type controls. The control is
        constructed from the method's parameters. Method and encoding are
        fixed to "POST" and "json" respectively.

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            f"{NAMESPACE}:{ctrl_name}",
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema,
        )

    def add_control_put(self, title, href, schema):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control name, method and
        encoding are fixed to "edit", "PUT" and "json" respectively.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            "edit", href, method="PUT", encoding="json", title=title, schema=schema
        )

    def add_control_delete(self, title, href):
        """
        Utility method for adding DELETE type controls. The control is
        constructed from the method's parameters. Control method is fixed to
        "DELETE", and control's name is read from the class attribute
        *DELETE_RELATION* which needs to be overridden by the child class.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        """

        self.add_control(
            f"{NAMESPACE}:delete",
            href,
            method="DELETE",
            title=title,
        )


class InventoryManagerBuilder(MasonBuilder):
    """
    A subclass of MasonBuilder that provides methods for adding application
    specific elements to the Mason object. This class is specific
    to the InventoryManager application.
    """

    def add_control_all_items(self) -> None:
        """
        Adds a control to the Mason object that links to the collection of all
        items in the database.
        """
        self.add_control(
            f"{NAMESPACE}:items-all",
            url_for("api.itemcollection"),
            method="GET",
            title="All items",
        )

    def add_control_all_warehouses(self) -> None:
        """
        Adds a control to the Mason object that links to the collection of all
        warehouses in the database.
        """
        self.add_control(
            f"{NAMESPACE}:warehouses-all",
            url_for("api.warehousecollection"),
            method="GET",
            title="All warehouses",
        )

    def add_control_all_stock(self) -> None:
        """
        Adds a control to the Mason object that links to the collection of all
        stock in the database.
        """
        self.add_control(
            f"{NAMESPACE}:stock-all",
            url_for("api.stockcollection"),
            method="GET",
            title="All stock",
        )

    def add_control_all_catalogue(self) -> None:
        """
        Adds a control to the Mason object that links to the collection of all
        catalogues in the database.
        """
        self.add_control(
            f"{NAMESPACE}:catalogues-all",
            url_for("api.cataloguecollection"),
            method="GET",
            title="All catalogue",
        )

    def add_control_all_locations(self) -> None:
        """
        Adds a control to the Mason object that links to the collection of all
        locations in the database.
        """
        self.add_control(
            f"{NAMESPACE}:locations-all",
            url_for("api.locationcollection"),
            method="GET",
            title="All locations",
        )

    def add_control_all_catalogue_item(self, item: Item) -> None:
        """Adds a control to the Mason object that links to the collection of all
        catalogue entries of a specific item.

        :param item: item to filter by
        """
        self.add_control(
            f"{NAMESPACE}:catalogue-item-all",
            url_for("api.catalogueitemcollection", item=item),
            method="GET",
            title="All catalogue entries for this item",
        )

    def add_control_get_item(self, item: Item) -> None:
        """Adds a control to the Mason object that links to a specific item.

        :param item: item to get
        """
        self.add_control(
            f"{NAMESPACE}:item",
            url_for("api.itemitem", item=item),
            method="GET",
            title="Get item",
        )

    def add_control_get_warehouse(self, warehouse: Warehouse) -> None:
        """Adds a control to the Mason object that links to a specific warehouse.

        :param warehouse: warehouses to get
        """
        self.add_control(
            f"{NAMESPACE}:warehouse",
            url_for("api.warehouseitem", warehouse=warehouse),
            method="GET",
            title="Get warehouse",
        )

    def add_control_all_stock_item(self, item: Item) -> None:
        """Adds a control to the Mason object that links to the collection of all
        stock entries of a specific item.

        :param item: item to filter stock by
        """
        self.add_control(
            f"{NAMESPACE}:stock-item-all",
            url_for("api.stockitemcollection", item=item),
            method="GET",
            title="All stock entries for this item",
        )

    def add_control_all_stock_warehouse(self, warehouse: Warehouse) -> None:
        """Adds a control to the Mason object that links to the collection of all
        stock entries of a specific warehouse.

        :param warehouse: warehouse to filter stock by
        """
        self.add_control(
            f"{NAMESPACE}:stock-warehouse-all",
            url_for("api.stockwarehousecollection", warehouse=warehouse),
            method="GET",
            title="All stock entries for this warehouse",
        )

    def add_control_all_catalogue_supplier(self, supplier) -> None:
        """Adds a control to the Mason object that links to the catalogue entries
        filtered by supplier name.

        :param supplier: supplier name to use as filter
        """
        self.add_control(
            f"{NAMESPACE}:catalogue-supplier-all",
            url_for("api.cataloguesuppliercollection", supplier=supplier),
            method="GET",
            title="All catalogue entries filtered by supplier name",
        )
