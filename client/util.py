import curses

def menu(window, menu_options=["Option 1", "Option 2", "Option 3"], menu_title="Select an option:"):
    selected_option = 0
    top_line = 0 
    max_y, max_x = window.getmaxyx()

    window.keypad(True)

    while True:
        window.clear()
        window.addstr(2, 0, menu_title, curses.A_NORMAL)

        for i in range(top_line, min(top_line + max_y - 4, len(menu_options))):
            option = menu_options[i]
            if i == selected_option:
                window.addstr(4 + i - top_line, 2, f"> {option}", curses.A_REVERSE)
            else:
                window.addstr(4 + i - top_line, 2, f"> {option}", curses.A_NORMAL)

        window.refresh()
        key = window.getch()
        if key == curses.KEY_UP and selected_option > 0:
            selected_option -= 1
            if selected_option < top_line:
                top_line = selected_option
        elif key == curses.KEY_DOWN and selected_option < len(menu_options) - 1:
            selected_option += 1
            if selected_option >= top_line + max_y - 4:
                top_line = selected_option - (max_y - 5)
        elif key == ord('\n'):
            return menu_options[selected_option]

def ask_inputs(window, prompts):
    for i, prompt in enumerate(prompts):
        yield _ask_input(window, prompt, shift_y=i*2)
    window.clear()
    window.refresh()

def _ask_input(window, prompt, shift_y = 0):
    window.addstr(0 + shift_y, 0, prompt)
    window.refresh()
    curses.echo()
    user_input = window.getstr(1 + shift_y, 0).decode('utf-8')
    curses.noecho()
    return user_input            


def display_dict(window, dictionary, title):
    max_y, max_x = window.getmaxyx()
    window.clear()
    window.box()
    window.addstr(0, 1, title[:max_x-2], curses.A_BOLD)
    
    pos_y = 1 
    for key, value in dictionary.items():
        line = f"{key}: {value}"
        if pos_y < max_y - 1: 
            window.addstr(pos_y, 1, line[:max_x-2]) 
            pos_y += 1
        else:
            break
    window.refresh()



def display_nested_dict(window, nested_dictionary, title):
    max_y, max_x = window.getmaxyx()
    window.clear()
    window.box()
    window.addstr(0, 1, title[:max_x-2], curses.A_BOLD)

    pos_y = 1
    for dictionary in nested_dictionary:
        if pos_y >= max_y - 1:
            break  

        dictionary_clean = {k: v for k, v in dictionary.items() if "@" not in k}
        for key, value in dictionary_clean.items():
            line = f"{key}: {value}"
            if pos_y < max_y - 1:
                window.addstr(pos_y, 1, line[:max_x-2])
                pos_y += 1
            else:
                break  
        
        if pos_y < max_y - 1:
            window.hline(pos_y, 1, "-", max_x-2)  # Draw a horizontal line within the bounds
            pos_y += 1
        else:
            break

    window.refresh()