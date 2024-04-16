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