import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from error import APIError
import curses
from curses import wrapper
import json
from util import menu, ask_inputs, display_dict, display_nested_dict

INVENTORY_MANAGER_API = "http://localhost:5000"
AUX_API = "http://localhost:5001"
NAMESPACE = "invmanager"

def main(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Handheld Client:", curses.A_BOLD)
    stdscr.refresh()
    
    menu_window = curses.newwin(10, 40, 1, 0)
    user_entry_window = curses.newwin(10, 40, 11, 0)
    stock_window = curses.newwin(20, 40, 1, 40)
    stock_item_window = curses.newwin(20, 40, 1, 80)

    while True:
        selected_option = menu(menu_window, ["Enter Stock", "Scan Stock", "Exit"])
        if selected_option == "Enter Stock":
            warehouse_id, item_name = ask_inputs(user_entry_window, ["Enter Warehouse ID: ", "Enter Item Name: "])
        elif selected_option == "Scan Stock":
            image_path = list(ask_inputs(user_entry_window, ["Enter path to QR image: "]))[0]
            warehouse_id, item_name = scan_stock(stdscr, image_path)
        elif selected_option == "Exit":
            break

        while True:
            menu_title = f"Selected {item_name} in warehouse {warehouse_id}"
            stock_response, stock_response_clean = get_stock(warehouse_id, item_name)
            display_dict(stock_window, stock_response_clean, title="STOCK")

            selected_option = menu(menu_window, ["Change Quantity", "Change Price", "Print QR Code", "View Item Info", "Item-Stock in other Warehouses", "Back"], menu_title=menu_title)
            if selected_option == "Change Quantity":
                handle_change_quantity(stdscr, menu_window, user_entry_window, warehouse_id, item_name)
            elif selected_option == "Change Price":
                handle_change_price(stdscr, user_entry_window, warehouse_id, item_name)
            elif selected_option == "Print QR Code":
                print_qr_code(stdscr, warehouse_id, item_name)
            elif selected_option == "View Item Info":
                view_item_info(stdscr, stock_window, item_name)
            elif selected_option == "Item-Stock in other Warehouses":
                item_stock_response = follow_relation(stock_response, "stock-item-all")
                display_nested_dict(stock_item_window, item_stock_response["items"], title="ITEM-STOCK")
            elif selected_option == "Back":
                menu_window.clear()
                break

def get_stock(warehouse_id, item_name):
    try:
        init_response = requests.get(INVENTORY_MANAGER_API + "/api")
        init_response.raise_for_status()
        controls = init_response.json()['@controls']
        stock_url = controls[f"{NAMESPACE}:stock"]['href'].format(warehouse_id=warehouse_id, item_name=item_name)
        
        stock_response = requests.get(stock_url)
        stock_response.raise_for_status()
        stock_data = stock_response.json()
        stock_data_clean = {k: v for k, v in stock_data.items() if not k.startswith('@')}
        return stock_data, stock_data_clean
    except requests.RequestException as e:
        print(f"Request failed: {str(e)}")
        return {}, {}

def handle_change_quantity(stdscr, menu_window, user_entry_window, warehouse_id, item_name):
    quantity_option = menu(menu_window, ["Add 1", "Add 5", "Remove 1", "Remove 5", "Enter Custom Amount", "Back"], menu_title="Update Stock Quantity")
    if quantity_option.startswith("Add") or quantity_option.startswith("Remove"):
        modify_quantity(stdscr, warehouse_id, item_name, quantity_option)
    elif quantity_option == "Enter Custom Amount":
        custom_amount_input = next(ask_inputs(user_entry_window, ["Enter Custom Amount: "]), None)
        if custom_amount_input:
            custom_amount = int(custom_amount_input)
            action_type = menu(menu_window, ["Add", "Remove"], menu_title="Add or Remove?")
            modify_quantity(stdscr, warehouse_id, item_name, f"{action_type} {custom_amount}")
        else:
            stdscr.addstr(20, 0, "No amount entered.")
    stdscr.refresh()

def handle_change_price(stdscr, user_entry_window, warehouse_id, item_name):
    price_input = next(ask_inputs(user_entry_window, ["Enter New Price: "]), None)
    if price_input:
        new_price = float(price_input)
        update_price(stdscr, warehouse_id, item_name, new_price)
    else:
        stdscr.addstr(20, 0, "No price entered.")
    stdscr.refresh()

def modify_quantity(stdscr, warehouse_id, item_name, action):
    quantity = int(action.split()[1])
    if "Add" in action:
        update_stock(stdscr, warehouse_id, item_name, quantity)
    elif "Remove" in action:
        update_stock(stdscr, warehouse_id, item_name, -quantity)

def update_stock(stdscr, warehouse_id, item_name, quantity):
    try:
        stock_response, _ = get_stock(warehouse_id, item_name)
        update_url = stock_response['@controls'][f"{NAMESPACE}:update-stock"]['href']
        update_data = {'quantity': quantity}
        response = requests.put(update_url, json=update_data)
        response.raise_for_status()
        stdscr.addstr(20, 0, "Stock updated successfully.")
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Request issue: {str(e)}")

def update_price(stdscr, warehouse_id, item_name, new_price):
    try:
        stock_response, _ = get_stock(warehouse_id, item_name)
        update_url = stock_response['@controls'][f"{NAMESPACE}:update-price"]['href']
        update_data = {'price': new_price}
        response = requests.put(update_url, json=update_data)
        response.raise_for_status()
        stdscr.addstr(20, 0, "Price updated successfully.")
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Request issue: {str(e)}")

def scan_stock(stdscr, user_entry_window):
    image_path = list(ask_inputs(user_entry_window, ["Enter path to QR image: "]))[0]
    try:
        with open(image_path, 'rb') as file:
            files = {'image': file}
            response = requests.post(f"{AUX_API}/api/qrRead/", files=files)
            response.raise_for_status()
            stock_info = response.json()
            return stock_info['warehouse_id'], stock_info['item_name']
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Failed to scan stock: {str(e)}")
        return None, None

def print_qr_code(stdscr, warehouse_id, item_name):
    try:
        response = requests.get(f"{AUX_API}/api/qrGenerate/?warehouse_id={warehouse_id}&item_name={item_name}")
        response.raise_for_status()
        with open('output_qr.png', 'wb') as f:
            f.write(response.content)
        stdscr.addstr(20, 0, "QR Code saved as 'output_qr.png'.")
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Failed to print QR code: {str(e)}")

def view_item_info(stdscr, stock_window, item_name):
    try:
        response = requests.get(f"{INVENTORY_MANAGER_API}/api/items/{item_name}/")
        response.raise_for_status()
        item_details = response.json()
        display_dict(stock_window, item_details, title="Item Details")
    except requests.RequestException as e:
        stdscr.addstr(20, 0, f"Failed to retrieve item details: {str(e)}")

def follow_relation(response, relation):
    relation_url = response['@controls'][f"{NAMESPACE}:{relation}"]['href']
    relation_response = requests.get(relation_url)
    return relation_response.json()

if __name__ == "__main__":
    wrapper(main)