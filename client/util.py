import curses

def menu(window,menu_options = ["Option 1", "Option 2", "Option 3"], menu_title = "Select an option:"):
    selected_option = 0
    window.keypad(True)

    while True:
        window.addstr(2, 0, menu_title, curses.A_NORMAL)
        
        for i, option in enumerate(menu_options):
            if i == selected_option:
                window.addstr(4 + i, 2, f"> {option}", curses.A_REVERSE)
            else:
                window.addstr(4 + i, 2, f"> {option}", curses.A_NORMAL)
        
        window.refresh()
        
        key = window.getch()
        if key == curses.KEY_UP:
            selected_option = (selected_option - 1) % len(menu_options)
        elif key == curses.KEY_DOWN:
            selected_option = (selected_option + 1) % len(menu_options)
        elif key == ord('\n'):
            chosen_option = menu_options[selected_option]
            return chosen_option

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
    window.addstr(0, 1, title, curses.A_BOLD)
    
    pos_y = 1 
    for i, (key, value) in enumerate(dictionary.items()):
        line = f"{key}: {value}"
        if pos_y < max_y - 2:  
            window.addstr(pos_y, 1, line[:max_x-2])  # Clip the line to fit the window width
            pos_y += 1
        else:
            break  # Stop adding new lines if we run out of space



def display_nested_dict(window, nested_dictionary, title):
    window.clear()
    window.box()
    window.addstr(0, 1, title, curses.A_BOLD)
    i = 1
    for dictionary in nested_dictionary:
        dictionary_clean = {k: v for k, v in dictionary.items() if "@" not in k}
        for key, value in dictionary_clean.items():
            window.addstr(i, 1, f"{key}: {value}")
            i += 1
        #draw horizontal line
        window.hline(i, 1, "-", 38)
        i+=1
        window.refresh()