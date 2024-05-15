"""
This is the main file for the client application. 
This file will be used to interact with the user and send requests to the server.

TODO's: 
- modify_quantity: add or remove quantity, don't just change to number selected
- error handling
- add stock response clean as a global variable to get quantity in price put
- add timeout arguments
- issue with view item info window refresh - shift to the right
- ask user for image or path to image that is sent to aux api and returns information
- Clear previous stock details windows when you use 'back' button
"""
import curses
from curses import wrapper
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from error import APIError
from util import menu, ask_inputs, display_dict, display_nested_dict


INVENTORY_MANAGER_API = "http://localhost:5000"
AUX_API = "http://localhost:5001"
NAMESPACE = "invmanager"

quantity = None
shelf_price = None

def main(stdscr):
    """
    Main function 

    :param stdscr: _description_
    :raises APIError: _description_
    :raises APIError: _description_
    :return: _description_
    """
#69

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
            try:
                warehouse_id = list(ask_inputs(user_entry_window, ["Enter Warehouse ID: "]))[0]
                warehouse_id = int(warehouse_id)
                item_name = list(ask_inputs(user_entry_window, ["Enter Item Name: "]))[0]
            except ValueError:
                stdscr.addstr(20, 0, "Invalid warehouse ID. Must be a number.")
                stdscr.refresh()
                continue

        elif selected_option == "Scan Stock":
            #ask user for image or path to image that is sent to aux api and returns information
            #TODO ADD FUNCTIONALITY

            image_path = list(ask_inputs(user_entry_window, ["Enter path to QR image: "]))[0]
            warehouse_id, item_name = scan_stock(stdscr, image_path)

        elif selected_option == "Exit":
            break

        while True:
            #new menu to interact with stock
            menu_title = f"Selected {item_name} in warehouse {warehouse_id}"
            stock_response, stock_response_clean = get_stock(warehouse_id, item_name)
            display_dict(stock_window, stock_response_clean, title = "STOCK")

            # Scan QR code as option? in addition to Print QR code
            selected_option = menu(menu_window, ["Change Quantity", "Change Price", "Print QR Code","View Item Info", "Item-Stock in other Warehouses","Back"], menu_title=f"Selected {item_name} in warehouse {warehouse_id}")
            if selected_option == "Change Quantity":
                quantity_option = menu(menu_window, ["Add 1", "Add 5", "Remove 1", "Remove 5", "Enter Custom Amount", "Back"], menu_title="Update Stock Quantity")
                if quantity_option.startswith("Add") or quantity_option.startswith("Remove"):
                    modify_quantity(stdscr, warehouse_id, item_name, quantity_option)
                elif quantity_option == "Enter Custom Amount":
                    try:
                        custom_amount_input = next(ask_inputs(user_entry_window, ["Enter Custom Amount: "]))
                        custom_amount = int(custom_amount_input)
                        action_type = menu(menu_window, ["Add", "Remove"], menu_title="Add or Remove?")
                        modify_quantity(stdscr, warehouse_id, item_name, f"{action_type} {custom_amount}")
                    except StopIteration:
                        stdscr.addstr(20, 0, "No amount entered.")
                    except ValueError:
                        stdscr.addstr(20, 0, "Invalid input. Please enter a valid number.")
                stdscr.refresh()
            elif selected_option == "Change Price":
                try:
                    price_input = next(ask_inputs(user_entry_window, ["Enter New Price: "]))
                    new_price = float(price_input)
                    update_price(stdscr, warehouse_id, item_name, new_price)
                except StopIteration:
                    stdscr.addstr(20, 0, "No price entered.")
                except ValueError:
                    stdscr.addstr(20, 0, "Invalid input. Please enter a valid number.")
                stdscr.refresh()
            elif selected_option == "Print QR Code":
                #Maybe return path to QR code. scan QR code and return image path, open image popup 
                print_qr_code(stdscr, warehouse_id, item_name)
            elif selected_option == "View Item Info":
                view_item_info(stdscr, stock_item_window, item_name)
            elif selected_option == "Item-Stock in other Warehouses":
                item_stock_response = follow_relation(stock_response, "stock-item-all")
                display_nested_dict(stock_item_window, item_stock_response["items"], title = "ITEM-STOCK")
            elif selected_option == "Back":
                menu_window.clear()
                stdscr.refresh()
                break


def get_stock(warehouse_id, item_name):
    """_summary_

    :param warehouse_id: _description_
    :param item_name: _description_
    :return: _description_
    """
    # get stock of item in warehouse

    stock_response = requests.get(INVENTORY_MANAGER_API + f"/api/stocks/{warehouse_id}/item/{item_name}/").json()
    stock_response_clean = {k: v for k, v in stock_response.items() if "@" not in k}
    NAMESPACE = list(stock_response["@namespaces"].keys())[0]
    return stock_response, stock_response_clean

def get_item_id_by_name(warehouse_id, item_name):
    """
    GET requests for the item ID from the Inventory Manager API by item name.

    :param item_name: The name of the item whose ID is required.
    :return: The ID of the item if found, else None.
    """
    try:
        url = f"{INVENTORY_MANAGER_API}/api/stocks/{warehouse_id}/item/{item_name}/"
        response = requests.get(url)
        response.raise_for_status()
        item_data = response.json()

        if 'item_id' in item_data:
            return item_data['item_id']
        else:
            print(f"No 'item_id' found in the response for item: {item_name}")
            return None
    except requests.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} for item: {item_name}")
        return None
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        return None

def modify_quantity(stdscr, warehouse_id, item_name, action):
    """
    Adds or removes quantity of stock for a given item in the warehouse.

    :param stdscr: The curses window object for displaying messages.
    :param warehouse_id: ID of the warehouse where the stock is stored.
    :param item_name: Name of the item to update.
    :param action: _description_
    """
    get_stock
    quantity = int(action.split()[1])
    if "Add" in action:
        update_stock(stdscr, warehouse_id, item_name, quantity)
    elif "Remove" in action:
        update_stock(stdscr, warehouse_id, item_name, -quantity)

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
    data = {'warehouse_id': warehouse_id, 'item_id': item_id, 'quantity': quantity}
    
    try:
        response = requests.put(url, json=data)
        if response.status_code in {200, 204}:
            stdscr.addstr(20, 0, "Stock updated successfully.")
        else:
            raise APIError(response.status_code, response.text, url)
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Network or request issue: {str(e)}")
    except APIError as api_error:
        error_message = str(api_error) if str(api_error) else "Unknown API error."
        stdscr.addstr(20, 0, error_message)
    stdscr.refresh()

def update_price(stdscr, warehouse_id, item_name, new_price):
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
    data = {'warehouse_id': warehouse_id, 'item_id': item_id, 'quantity': quantity, 'shelf_price': new_price} #need to somehow pass quantity with data

    try:
        response = requests.put(url, json=data)
        if response.status_code in {200, 204}:
            stdscr.addstr(20, 0, "Price updated successfully.")
        else:
            raise APIError(response.status_code, response.text, url)
        stdscr.refresh()
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Network or request issue: {str(e)}")
        stdscr.refresh()
    except APIError as api_error:
        error_message = str(api_error) if str(api_error) else "Unknown API error."
        stdscr.addstr(20, 0, error_message)
        stdscr.refresh()

def scan_stock(stdscr, user_entry_window):
    inputs = list(ask_inputs(user_entry_window, ["Enter path to QR image: "]))
    image_path = inputs[0] if inputs else None
    try:
        with open(image_path, 'rb') as file:
            files = {'image': file}
            response = requests.post(f"{AUX_API}/api/qrRead/", files=files)
            response.raise_for_status()
            stock_info = response.json()
            return stock_info['warehouse_id'], stock_info['item_name']
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Failed to scan stock: {str(e)}")
        stdscr.refresh()
        return None, None

def print_qr_code(stdscr, warehouse_id, item_name):
    response = requests.get(f"{AUX_API}/api/qrGenerate/?warehouse_id={warehouse_id}&item_name={item_name}")
    if response.status_code == 200:
        with open('output_qr.png', 'wb') as f:
            f.write(response.content)
        stdscr.addstr(20, 0, "QR Code saved as 'output_qr.png'.")
        stdscr.refresh()
    else:
        stdscr.addstr(20, 0, f"Failed to print QR code: {response.text}")
        stdscr.refresh()

def view_item_info(stdscr, stock_window, item_name):
    """_summary_

    :param stdscr: _description_
    :param stock_window: _description_
    :param item_name: _description_
    """
    response = requests.get(f"{INVENTORY_MANAGER_API}/api/items/{item_name}/")
    response_clean = {k: v for k, v in response.json().items() if "@" not in k}
    if response.status_code == 200:
        item_details = response_clean
        display_dict(stock_window, item_details, title="Item Details")
    else:
        stdscr.addstr(20, 0, "Failed to retrieve item details.")
        stdscr.refresh()

def follow_relation(response, relation):
    relation_url = response["@controls"][f"{NAMESPACE}:{relation}"]["href"]
    return requests.get(INVENTORY_MANAGER_API + relation_url).json()

if __name__ == "__main__":
    wrapper(main)
