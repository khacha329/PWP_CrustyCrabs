"""
This is the main file for the client application. This file will be used to interact with the user and send requests to the server.

TODO's: 
- Add request sessions?
- 
"""
import requests
from error import APIError
import curses
from curses import wrapper

from util import menu, ask_inputs, display_dict, display_nested_dict


INVENTORY_MANAGER_API = "http://localhost:5000"
AUX_API = "http://localhost:5001"
NAMESPACE = "invmanager"

session = requests.Session()

def main(stdscr):

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
            warehouse_id, item_name = ask_inputs(user_entry_window, ["Enter Warehouse ID: ", "Enter Item Name: "])


        elif selected_option == "Scan Stock":
            #ask user for image or path to image that is sent to aux api and returns information
            #TODO ADD FUNCTIONALITY

            image_path = list(ask_inputs(user_entry_window, ["Enter path to QR image: "]))[0]
            warehouse_id, item_name = 1, "Laptop-1"

        elif selected_option == "Exit":
            exit()
        

        while True:        
            #new menu to intercact with stock
            menu_title = f"Selected {item_name} in warehouse {warehouse_id}"
            stock_response, stock_response_clean = get_stock(warehouse_id, item_name)
            display_dict(stock_window, stock_response_clean, title = "STOCK")

            selected_option = menu(menu_window, ["Change Quantity", "Change Price", "Print QR Code","View Item Info","Item-Stock in other Warehouses","Back"], menu_title=f"Selected {item_name} in warehouse {warehouse_id}")
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
                price = ask_inputs(user_entry_window, ["Enter Price: "])

            elif selected_option == "Print QR Code":
                #Maybe
                print_qr_code(stdscr, warehouse_id, item_name)
            elif selected_option == "View Item Info":
                #maybe
                view_item_info(stdscr, stock_window, item_name)
            elif selected_option == "Item-Stock in other Warehouses":
                item_stock_response = follow_relation(stock_response, "stock-item-all")
                display_nested_dict(stock_item_window, item_stock_response["items"], title = "ITEM-STOCK")
            elif selected_option == "Back":
                menu_window.clear()
                break


def get_stock(warehouse_id, item_name):
    # get stock of item in warehouse

    stock_response = requests.get(INVENTORY_MANAGER_API + f"/api/stocks/{warehouse_id}/item/{item_name}/").json()
    stock_response_clean = {k: v for k, v in stock_response.items() if "@" not in k}
    NAMESPACE = list(stock_response["@namespaces"].keys())[0]
    return stock_response, stock_response_clean

def modify_quantity(stdscr, warehouse_id, item_name, action):
    quantity = int(action.split()[1])
    if "Add" in action:
        update_stock(stdscr, warehouse_id, item_name, quantity)
    elif "Remove" in action:
        update_stock(stdscr, warehouse_id, item_name, -quantity)

def update_stock(stdscr, warehouse_id, item_name, quantity):
    url = f"{INVENTORY_MANAGER_API}/api/stocks/{warehouse_id}/item/{item_name}/update"
    data = {'quantity': quantity}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        if response.status_code == 201:
            stdscr.addstr(20, 0, "Stock updated successfully.")
        else:
            stdscr.addstr(20, 0, f"Failed to update stock: {response.text}")
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Request failed: {str(e)}")
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
    response = requests.get(f"{INVENTORY_MANAGER_API}/api/items/{item_name}/")
    if response.status_code == 200:
        item_details = response.json()
        display_dict(stock_window, item_details, title="Item Details")
    else:
        stdscr.addstr(20, 0, "Failed to retrieve item details.")
        stdscr.refresh()

def follow_relation(response, relation):
    relation_url = response["@controls"][f"{NAMESPACE}:{relation}"]["href"]
    return requests.get(INVENTORY_MANAGER_API + relation_url).json()

if __name__ == "__main__":
    wrapper(main)
