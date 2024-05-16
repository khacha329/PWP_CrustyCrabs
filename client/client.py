"""
This is the main file for the client application. 
This file will be used to interact with the user and send requests to the server.

"""

import curses
from curses import wrapper
import requests
from requests.exceptions import Timeout, RequestException
from error import APIError
from util import menu, ask_inputs, display_dict, display_nested_dict
from client_constants import INVENTORY_MANAGER_API, AUX_API, NAMESPACE, TIMEOUT_DURATION


def main(stdscr):
    """
    The main function of the client application which handles the interface and user interactions.
    It manages the display and navigation through various stock management features using the curses library.

    :param stdscr: The curses window object for displaying messages.
    """
    # 69

    stdscr.clear()
    stdscr.addstr(0, 0, "Handheld Client:", curses.A_BOLD)
    stdscr.refresh()
    # add window for menu and pass to menu function
    menu_window = curses.newwin(10, 40, 1, 0)
    user_entry_window = curses.newwin(10, 40, 11, 0)
    stock_window = curses.newwin(20, 40, 1, 40)
    stock_item_window = curses.newwin(20, 40, 1, 80)

    while True:
        selected_option = menu(menu_window, ["Enter Stock", "Scan Stock", "Exit"])

        if selected_option == "Enter Stock":
            input_valid = False
            while not input_valid:
                try:
                    warehouse_id = list(
                        ask_inputs(user_entry_window, ["Enter Warehouse ID: "])
                    )[0]
                    warehouse_id = int(warehouse_id)
                    item_name = list(ask_inputs(user_entry_window, ["Enter Item Name: "]))[0]
                    input_valid = True
                except ValueError:
                    stdscr.addstr(20, 0, "Invalid input. Please enter a valid number.")
                    stdscr.refresh()

        elif selected_option == "Scan Stock":
            warehouse_id, item_name = scan_stock(stdscr, user_entry_window)
            if warehouse_id is None or item_name is None:
                stdscr.addstr(20, 0, "Failed to scan stock. Try again.")
                stdscr.refresh()
                continue

        elif selected_option == "Exit":
            break

        while True:
            # new menu to interact with stock
            menu_title = f"Selected {item_name} in warehouse {warehouse_id}"
            stock_response, stock_response_clean, current_quantity = get_stock(
                warehouse_id, item_name
            )
            display_dict(stock_window, stock_response_clean, title="STOCK")

            selected_option = menu(
                menu_window,
                [
                    "Change Quantity",
                    "Change Price",
                    "Print QR Code",
                    "View Item Info",
                    "Item-Stock in other Warehouses",
                    "Back",
                ],
                menu_title=f"Selected {item_name} in warehouse {warehouse_id}",
            )
            if selected_option == "Change Quantity":
                quantity_option = menu(
                    menu_window,
                    [
                        "Add 1",
                        "Add 5",
                        "Remove 1",
                        "Remove 5",
                        "Enter Custom Amount",
                        "Back",
                    ],
                    menu_title="Update Stock Quantity",
                )
                if quantity_option.startswith("Add") or quantity_option.startswith(
                    "Remove"
                ):
                    current_quantity = modify_quantity(
                        stdscr,
                        warehouse_id,
                        item_name,
                        quantity_option,
                        current_quantity,
                    )
                elif quantity_option == "Enter Custom Amount":
                    try:
                        custom_amount_input = next(
                            ask_inputs(user_entry_window, ["Enter Custom Amount: "])
                        )
                        custom_amount = int(custom_amount_input)
                        action_type = menu(
                            menu_window, ["Add", "Remove"], menu_title="Add or Remove?"
                        )
                        current_quantity = modify_quantity(
                            stdscr,
                            warehouse_id,
                            item_name,
                            f"{action_type} {custom_amount}",
                            current_quantity,
                        )
                    except StopIteration:
                        stdscr.addstr(20, 0, "No amount entered.")
                    except ValueError:
                        stdscr.addstr(
                            20, 0, "Invalid input. Please enter a valid number."
                        )
                stdscr.refresh()
            elif selected_option == "Change Price":
                try:
                    price_input = next(
                        ask_inputs(user_entry_window, ["Enter New Price: "])
                    )
                    new_price = float(price_input)
                    update_price(
                        stdscr, warehouse_id, item_name, current_quantity, new_price
                    )
                except StopIteration:
                    stdscr.addstr(20, 0, "No price entered.")
                except ValueError:
                    stdscr.addstr(20, 0, "Invalid input. Please enter a valid number.")
                stdscr.refresh()
            elif selected_option == "Print QR Code":
                print_qr_code(stdscr, warehouse_id, item_name)
            elif selected_option == "View Item Info":
                view_item_info(stdscr, stock_item_window, item_name)
            elif selected_option == "Item-Stock in other Warehouses":
                item_stock_response = follow_relation(stock_response, "stock-item-all")
                display_nested_dict(
                    stock_item_window, item_stock_response["items"], title="ITEM-STOCK"
                )
            elif selected_option == "Back":
                menu_window.clear()
                stdscr.refresh()
                break


def get_stock(warehouse_id, item_name):
    """ Get stock of item in warehouse

    :param warehouse_id: ID of the warehouse where the stock is stored.
    :param item_name: The name of the item whose ID is required.
    :return: Tuple containing the stock response, cleaned stock response, and current quantity if available.
    """
    try:
        stock_response = requests.get(
            INVENTORY_MANAGER_API + f"/api/stocks/{warehouse_id}/item/{item_name}/",
            timeout=TIMEOUT_DURATION,
        ).json()
    except Timeout:
        print(f"The request timed out after {TIMEOUT_DURATION} seconds")
        stock_response = None
        return None
    except RequestException as e:
        print(f"An error occurred while carrying out the request: {e}")
        stock_response = None
        return None
    stock_quantity = stock_response["quantity"]
    stock_shelf_price = stock_response["shelf_price"]
    stock_response_clean = {k: v for k, v in stock_response.items() if "@" not in k}
    NAMESPACE = list(stock_response["@namespaces"].keys())[0]
    return stock_response, stock_response_clean, stock_quantity


def get_item_id_by_name(warehouse_id, item_name):
    """
    GET requests for the item ID from the Inventory Manager API by item name.

    :param item_name: The name of the item whose ID is required.
    :return: The ID of the item if found, else None.
    """
    try:
        url = f"{INVENTORY_MANAGER_API}/api/stocks/{warehouse_id}/item/{item_name}/"
        response = requests.get(url=url, timeout=TIMEOUT_DURATION)
        response.raise_for_status()
        item_data = response.json()

        if "item_id" in item_data:
            return item_data["item_id"]
        else:
            print(f"No 'item_id' found in the response for item: {item_name}")
            return None
    except Timeout:
        print(f"Error! Request Timed Out after {TIMEOUT_DURATION} seconds")
        return None
    except requests.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} for item: {item_name}")
        return None
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        return None


def modify_quantity(stdscr, warehouse_id, item_name, action, current_quantity):
    """
    Adds or removes quantity of stock for a given item in the warehouse.

    :param stdscr: The curses window object for displaying messages.
    :param warehouse_id: ID of the warehouse where the stock is stored.
    :param item_name: Name of the item to update.
    :return: The new quantity of stock
    """
    quantity = int(action.split()[1])
    if "Add" in action:
        quantity = quantity + current_quantity
        update_stock(stdscr, warehouse_id, item_name, quantity)
    elif "Remove" in action:
        quantity = -quantity + current_quantity
        update_stock(stdscr, warehouse_id, item_name, quantity)
    modified_quantity = quantity
    return modified_quantity


def update_stock(stdscr, warehouse_id, item_name, quantity):
    """
    Updates the stock quantity for a given item in a warehouse.

    :param stdscr: The curses window object for displaying messages.
    :param warehouse_id: ID of the warehouse where the stock is stored.
    :param item_name: Name of the item to update.
    :param quantity: Quantity to update in the stock.
    """
    item_id = get_item_id_by_name(warehouse_id, item_name)

    if item_id is None:
        stdscr.addstr(20, 0, "Failed to find the item ID for the given item name.")
        stdscr.refresh()
        return

    url = f"{INVENTORY_MANAGER_API}/api/stocks/{warehouse_id}/item/{item_name}/"
    data = {"warehouse_id": warehouse_id, "item_id": item_id, "quantity": quantity}

    try:
        response = requests.put(url, json=data, timeout=TIMEOUT_DURATION)
        if response.status_code in {200, 204}:
            stdscr.addstr(20, 0, "Stock updated successfully.")
        else:
            raise APIError(response.status_code, response.text, url)
    except Timeout as t:
        stdscr.addstr(20, 0, f"Request Timed Out: {str(t)}")
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Network or request issue: {str(e)}")
    except APIError as api_error:
        error_message = str(api_error) if str(api_error) else "Unknown API error."
        stdscr.addstr(20, 0, error_message)
    stdscr.refresh()


def update_price(stdscr, warehouse_id, item_name, modifeid_quantity, new_price):
    """
    Updates the price of a given item in a warehouse.

    :param stdscr: The curses window object for displaying messages.
    :param warehouse_id: ID of the warehouse where the item is stored.
    :param item_name: Name of the item to update.
    :param new_price: New price to set for the item.
    """
    item_id = get_item_id_by_name(warehouse_id, item_name)

    if item_id is None:
        stdscr.addstr(20, 0, "Failed to find the item ID for the given item name.")
        stdscr.refresh()
        return

    url = f"{INVENTORY_MANAGER_API}/api/stocks/{warehouse_id}/item/{item_name}/"
    data = {
        "warehouse_id": warehouse_id,
        "item_id": item_id,
        "quantity": modifeid_quantity,
        "shelf_price": new_price,
    }

    try:
        response = requests.put(url, json=data, timeout=TIMEOUT_DURATION)
        if response.status_code in {200, 204}:
            stdscr.addstr(20, 0, "Price updated successfully.")
        else:
            raise APIError(response.status_code, response.text, url)
        stdscr.refresh()
    except Timeout as t:
        stdscr.addstr(20, 0, f"Request TimedOut: {str(t)}")
        stdscr.refresh()
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Network or request issue: {str(e)}")
        stdscr.refresh()
    except APIError as api_error:
        error_message = str(api_error) if str(api_error) else "Unknown API error."
        stdscr.addstr(20, 0, error_message)
        stdscr.refresh()


def scan_stock(stdscr, user_entry_window):
    """
    Scans the current stock.

    :param stdscr: The curses window object for displaying messages.
    :param user_entry_window: Window used by the user to interact with client.
    """
    inputs = list(ask_inputs(user_entry_window, ["Enter path to QR image: "]))
    image_path = inputs[0] if inputs else None
    try:
        with open(image_path, "rb") as file:
            files = {"image": file}
            response = requests.post(
                f"{AUX_API}/api/qrRead/", files=files, timeout=TIMEOUT_DURATION
            )
            response.raise_for_status()
            stock_info = response.json()
            return stock_info["warehouse_id"], stock_info["item_name"]
    except Timeout as t:
        stdscr.addstr(20, 0, f"Request TimedOut: {str(t)}")
        stdscr.refresh()
        return None, None
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Failed to scan stock: {str(e)}")
        stdscr.refresh()
        return None, None


def print_qr_code(stdscr, warehouse_id, item_name):
    """
    Print the QR-Code.

    :param stdscr: The curses window object for displaying messages.
    :param warehouse_id: ID of the warehouse where the item is stored.
    :param item_name: Name of the item to update.
    """
    try:
        response = requests.get(
            f"{AUX_API}/api/qrGenerate/?warehouse_id={warehouse_id}&item_name={item_name}",
            timeout=TIMEOUT_DURATION,
        )
        if response.status_code == 200:
            with open("output_qr.png", "wb") as f:
                f.write(response.content)
            stdscr.addstr(20, 0, "QR Code saved as 'output_qr.png'.")
            stdscr.refresh()
        else:
            stdscr.addstr(20, 0, f"Failed to print QR code: {response.text}")
            stdscr.refresh()
    except Timeout as t:
        stdscr.addstr(20, 0, f"Request TimedOut: {str(t)}")
        stdscr.refresh()
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Failed to print QR Code: {str(e)}")
        stdscr.refresh()


def view_item_info(stdscr, stock_window, item_name):
    """View the info of a given item

    :param stdscr: The curses window object for displaying messages.
    :param stock_window: The curses window to display stock information
    :param item_name: Name of stock item
    """
    try:
        response = requests.get(
            url=f"{INVENTORY_MANAGER_API}/api/items/{item_name}/",
            timeout=TIMEOUT_DURATION,
        )
    except Timeout as t:
        stdscr.addstr(20, 0, f"Request Timed Out: {str(t)}")
        stdscr.refresh()
    response_clean = {k: v for k, v in response.json().items() if "@" not in k}
    if response.status_code == 200:
        item_details = response_clean
        display_dict(stock_window, item_details, title="Item Details")
    else:
        stdscr.addstr(20, 0, "Failed to retrieve item details.")
        stdscr.refresh()


def follow_relation(response, relation):
    """Follow the link relation in the given response

    :param response: The API response
    :param relation: The link relation that needs to be followed
    """
    relation_url = response["@controls"][f"{NAMESPACE}:{relation}"]["href"]
    try:
        return requests.get(
            INVENTORY_MANAGER_API + relation_url, timeout=TIMEOUT_DURATION
        ).json()
    except Timeout:
        print("Request Timed Out")
        return None
    # return requests.get(INVENTORY_MANAGER_API + relation_url).json()


if __name__ == "__main__":
    wrapper(main)
