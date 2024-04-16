"""
This is the main file for the client application. This file will be used to interact with the user and send requests to the server.
"""
import requests

import curses
from curses import wrapper

from util import menu, ask_inputs, display_dict, display_nested_dict


INVENTORY_MANAGER_API = "http://localhost:5000"
AUX_API = "http://localhost:5001"
NAMESPACE = "invmanager"
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

            warehouse_id, item_name = 1, "Laptop-1"

        elif selected_option == "Exit":
            exit()
        

        while True:        
            #new menu to intercact with stock
            menu_title = f"Selected {item_name} in warehouse {warehouse_id}"
            stock_response, stock_response_clean = get_stock(warehouse_id, item_name)
            display_dict(stock_window, stock_response_clean, title = "STOCK")

            selected_option = menu(menu_window, ["Change Quantity", "Change Price", "Print QR Code","View Item Info","Item-Stock in other Warehouses","Back"], menu_title = menu_title)
            if selected_option == "Change Quantity":
                quantity = ask_inputs(user_entry_window, ["Enter Quantity: "])
            elif selected_option == "Change Price":
                price = ask_inputs(user_entry_window, ["Enter Price: "])

            elif selected_option == "Print QR Code":
                #TODO ADD FUNCTIONALITY
                pass
            elif selected_option == "View Item Info":
                #TODO ADD FUNCTIONALITY
                pass
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

def follow_relation(response, relation):
    relation_url = response["@controls"][f"{NAMESPACE}:{relation}"]["href"]
    return requests.get(INVENTORY_MANAGER_API + relation_url).json()

if __name__ == "__main__":
    wrapper(main)

