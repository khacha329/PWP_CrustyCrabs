import curses
from curses import wrapper
from util import menu, ask_inputs





def main(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Handheld Client:", curses.A_BOLD)
    stdscr.refresh()
    # add window for menu and pass to menu function
    menu_window = curses.newwin(10, 40, 1, 0)
    user_entry_window = curses.newwin(10, 40, 11, 0)
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
                #TODO ADD FUNCTIONALITY
                pass
            elif selected_option == "Back":
                menu_window.clear()
                break

    




    stdscr.refresh()
    curses.napms(5000)

    
    
    #warehouse_id = stdscr.getch()



   

wrapper(main)


