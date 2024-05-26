import json
import curses
import curses.textpad
import os

class ConfigOption:
    """
    Represents a configuration option.

    Attributes:
        name (str): The name of the option.
        option_type (str): The type of the option (e.g., 'bool', 'group', 'int', 'string', 'multiple_choice').
        default (any): The default value of the option.
        dependencies (list): A list of dependencies that this option depends on.
        options (list): A list of sub-options if this option is a group.
        choices (list): A list of choices if this option is a multiple choice option.
        expanded (bool): Indicates whether a group option is expanded or not.
    """

    def __init__(self, name, option_type, default=None, dependencies=None, options=None, choices=None, expanded=False):
        self.name = name
        self.option_type = option_type
        self.value = default
        self.default = default
        self.dependencies = dependencies or []
        self.options = options or []
        self.choices = choices or []
        self.expanded = expanded

    def to_dict(self):
        """Convert the option to a dictionary format."""
        return {
            'name': self.name,
            'type': self.option_type,
            'default': self.default,
            'dependencies': self.dependencies,
            'options': [opt.to_dict() for opt in self.options],
            'choices': self.choices
        }

class pyconfig:
    """
    Manages configuration options, rendering them in a text-based UI using curses.

    Attributes:
        config_files (list): List of configuration file paths.
        output_file (str): Path to the output file where the configuration will be saved.
        custom_save_func (callable): Custom function to be called when saving the configuration.
        options (list): List of configuration options.
        config_name (str): Name of the configuration.
    """

    def __init__(self, config_files, output_file="output_config.json", custom_save_func=None):
        self.config_files = config_files
        self.output_file = output_file
        self.custom_save_func = custom_save_func
        self.options = []
        self.config_name = ""
        self.load_config()
        self.apply_saved_config()

    def load_config(self):
        """Load configuration from the specified files."""
        for config_file in self.config_files:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                self.config_name = config_data.get('name', 'Configuration')
                self.parse_options(config_data['options'], self.options)
                for include_file in config_data.get('include', []):
                    with open(include_file, 'r') as f:
                        extra_config_data = json.load(f)
                        self.parse_options(extra_config_data['options'], self.options)

    def parse_options(self, options_data, parent_list):
        """Parse options from JSON data."""
        for option_data in options_data:
            option = ConfigOption(
                name=option_data['name'],
                option_type=option_data['type'],
                default=option_data.get('default'),
                dependencies=option_data.get('dependencies'),
                choices=option_data.get('choices', []),
                expanded=option_data.get('expanded', False),
                options=[]
            )
            if option.option_type == 'group' and 'options' in option_data:
                self.parse_options(option_data['options'], option.options)
            parent_list.append(option)

    def apply_saved_config(self):
        """Apply saved configuration values from the output file."""
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r') as f:
                saved_config = json.load(f)
                self.apply_config_to_options(self.options, saved_config)

    def apply_config_to_options(self, options, saved_config):
        """Apply saved configuration values to the options."""
        for option in options:
            if option.option_type == 'group':
                self.apply_config_to_options(option.options, saved_config)
            elif option.name in saved_config:
                option.value = saved_config[option.name] if option.option_type != 'multiple_choice' else option.choices.index(saved_config[option.name])

    def is_option_visible(self, option):
        """Check if an option is visible based on its dependencies."""
        return all(self.is_dependency_met(dep) for dep in option.dependencies)

    def is_dependency_met(self, dependency_name):
        """Check if a dependency is met."""
        return any((opt.name == dependency_name and opt.value) or 
                   (opt.option_type == 'group' and any(sub_opt.name == dependency_name and sub_opt.value for sub_opt in opt.options)) 
                   for opt in self.options)

    def render_menu(self, stdscr, options, current_row, start_y=0, indent=0, idx=0, padding_left=4, initial_call=True, search_mode=False, search_query=""):
        """
        Render the configuration menu.

        Args:
            stdscr: Curses window object.
            options (list): List of options to render.
            current_row (int): The current highlighted row.
            start_y (int): The starting y position.
            indent (int): The current indentation level.
            idx (int): The current index in the option list.
            padding_left (int): The padding on the left side.
            initial_call (bool): Indicates if this is the initial call to render the menu.
            search_mode (bool): Indicates if search mode is active.
            search_query (str): The current search query.
        """
        padding_top = 2 if initial_call else 0
        current_y = start_y + padding_top
        max_y, max_x = stdscr.getmaxyx()
        visible_options = []

        for option in options:
            if not self.is_option_visible(option) or (search_mode and search_query.lower() not in option.name.lower() and option.option_type != 'group'):
                continue

            if option.option_type == 'group' and search_mode:
                nested_visible = [opt for opt in option.options if search_query.lower() in opt.name.lower()]
                if not nested_visible and search_query.lower() not in option.name.lower():
                    continue

            visible_options.append(option)
            if option.option_type == 'group':
                indicator = "[+]" if not option.expanded else "[-]"
                display_text = f"{indicator} {option.name}"
                self.display_option(stdscr, display_text, idx, current_row, current_y, indent, padding_left)
                current_y += 1
                idx += 1
                if option.expanded or search_mode:
                    nested_y, nested_idx, nested_visible = self.render_menu(stdscr, option.options, current_row, current_y, indent + 2, idx, padding_left, False, search_mode, search_query)
                    current_y, idx = nested_y, nested_idx
                    visible_options.extend(nested_visible)
            else:
                value_to_display = option.choices[option.value] if option.option_type == 'multiple_choice' else option.value or option.default
                display_text = f"{option.name}: {value_to_display}"
                if len(display_text) > max_x - indent - padding_left - 4:
                    display_text = display_text[:max_x - indent - padding_left - 7] + "..."
                self.display_option(stdscr, display_text, idx, current_row, current_y, indent, padding_left)
                current_y += 1
                idx += 1

        if search_mode:
            stdscr.addstr(max_y - 3, 2, f"Search: {search_query}")
            stdscr.addstr(max_y - 2, 2, "Press ESC to exit search")

        return current_y, idx, visible_options

    def display_option(self, stdscr, text, idx, current_row, y, indent, padding_left):
        """
        Display a single option in the menu.

        Args:
            stdscr: Curses window object.
            text (str): The text to display.
            idx (int): The current index in the option list.
            current_row (int): The current highlighted row.
            y (int): The y position to display the text.
            indent (int): The current indentation level.
            padding_left (int): The padding on the left side.
        """
        if idx == current_row:
            stdscr.attron(curses.color_pair(1))
        stdscr.addstr(y, indent + padding_left, " " * len(text))
        stdscr.addstr(y, indent + padding_left, text)
        if idx == current_row:
            stdscr.attroff(curses.color_pair(1))

    def run(self):
        """Run the configuration manager."""
        curses.wrapper(self.menu_loop)

    def menu_loop(self, stdscr):
        """
        Main loop for the menu.

        Args:
            stdscr: Curses window object.
        """
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        current_row = 0
        search_mode, search_query = False, ""
        while True:
            stdscr.clear()
            stdscr.border(0)
            stdscr.addstr(0, 2, f" {self.config_name} ")
            if not search_mode:
                stdscr.addstr(curses.LINES - 2, 2, " Press 's' to Save, 'q' to Exit, 'c' to Collapse Group, '/' to Search ")
            current_y, idx, visible_options = self.render_menu(stdscr, self.options, current_row, start_y=1, search_mode=search_mode, search_query=search_query)
            stdscr.refresh()
            key = stdscr.getch()

            if search_mode:
                if key in (curses.KEY_BACKSPACE, 127):
                    search_query = search_query[:-1]
                elif key == 27:
                    stdscr.timeout(100)
                    if stdscr.getch() == -1:
                        search_mode, search_query = False, ""
                    stdscr.timeout(-1)
                elif 32 <= key <= 126:
                    search_query += chr(key)
                elif key in (curses.KEY_UP, curses.KEY_DOWN):
                    current_row = (current_row + (-1 if key == curses.KEY_UP else 1)) % len(visible_options)
                elif key in (curses.KEY_ENTER, 10, 13):
                    self.handle_enter(visible_options, current_row, stdscr, search_mode)
            else:
                if key in (curses.KEY_UP, curses.KEY_DOWN):
                    current_row = (current_row + (-1 if key == curses.KEY_UP else 1)) % len(visible_options)
                elif key in (curses.KEY_ENTER, 10, 13):
                    self.handle_enter(visible_options, current_row, stdscr, search_mode)
                elif key == ord('s'):
                    self.save_config(stdscr)
                elif key == ord('q'):
                    break
                elif key == ord('c'):
                    current_row = self.collapse_current_group(visible_options, current_row)
                elif key == ord('/'):
                    search_mode, search_query, current_row = True, "", 0

    def handle_enter(self, options, row, stdscr, search_mode):
        """
        Handle the Enter key press.

        Args:
            options (list): List of options.
            row (int): The current row.
            stdscr: Curses window object.
            search_mode (bool): Indicates if search mode is active.
        """
        if not options:
            return
        selected_option = options[row]
        if selected_option.option_type == 'bool':
            selected_option.value = not selected_option.value
        elif selected_option.option_type == 'group':
            selected_option.expanded = not selected_option.expanded
        elif selected_option.option_type in ['int', 'string']:
            self.edit_option(stdscr, selected_option)
        elif selected_option.option_type == 'multiple_choice':
            self.edit_multiple_choice_option(stdscr, selected_option)

        # Remove setting search_mode to False to stay in search mode
        # if not search_mode:
        #     search_mode = False

    def edit_option(self, stdscr, option):
        """
        Edit a configuration option.

        Args:
            stdscr: Curses window object.
            option (ConfigOption): The option to edit.
        """
        original_value = option.value
        curses.curs_set(1)
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        stdscr.addstr(0, 0, f"Editing {option.name} (current value: {option.value}): ")
        stdscr.addstr(1, 0, "Press ENTER to save, ESC or 'q' to cancel.")
        editwin = curses.newwin(3, max_x - 2, 2, 1)
        curses.textpad.rectangle(stdscr, 1, 0, 4, max_x - 1)
        stdscr.addstr(max_y - 2, 2, " Press 'q' to Cancel ")
        stdscr.refresh()
        box = curses.textpad.Textbox(editwin, insert_mode=True)

        def validate_input(ch):
            if ch == ord('q'):
                raise KeyboardInterrupt
            elif ch in (curses.ascii.CR, curses.ascii.NL):
                return 7
            return ch

        try:
            box.edit(validate_input)
        except KeyboardInterrupt:
            option.value = original_value
            curses.curs_set(0)
            return
        
        new_value = box.gather().replace('\n', '').strip()
        if option.option_type == 'int':
            try:
                option.value = int(new_value)
            except ValueError:
                option.value = original_value
        elif option.option_type == 'string':
            option.value = new_value
        curses.curs_set(0)

    def edit_multiple_choice_option(self, stdscr, option):
        """
        Edit a multiple choice configuration option.

        Args:
            stdscr: Curses window object.
            option (ConfigOption): The option to edit.
        """
        curses.curs_set(0)
        current_choice = option.value if option.value is not None else 0
        original_choice = option.value
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Editing {option.name} (current choice: {option.choices[current_choice]}): ")
            stdscr.addstr(1, 0, "Use UP/DOWN to change choice, ENTER to save, ESC or 'q' to cancel.")
            stdscr.addstr(curses.LINES - 2, 2, " Press 'q' to Cancel ")
            for idx, choice in enumerate(option.choices):
                if idx == current_choice:
                    stdscr.attron(curses.color_pair(1))
                if 3 + idx < stdscr.getmaxyx()[0]:
                    stdscr.addstr(3 + idx, 2, " " * (len(choice) + 4))
                    stdscr.addstr(3 + idx, 2, choice)
                if idx == current_choice:
                    stdscr.attroff(curses.color_pair(1))
            stdscr.refresh()
            key = stdscr.getch()
            if key == curses.KEY_UP and current_choice > 0:
                current_choice -= 1
            elif key == curses.KEY_DOWN and current_choice < len(option.choices) - 1:
                current_choice += 1
            elif key in (curses.KEY_ENTER, 10, 13):
                option.value = current_choice
                break
            elif key in (27, ord('q')):
                option.value = original_choice
                break

    def collapse_current_group(self, flat_options, current_row):
        """
        Collapse the currently selected group.

        Args:
            flat_options (list): Flattened list of options.
            current_row (int): The current row index.

        Returns:
            int: The new current row index.
        """
        selected_option = flat_options[current_row]
        if selected_option.option_type == 'group':
            selected_option.expanded = False
            return current_row
        for idx, option in enumerate(flat_options):
            if option.option_type == 'group' and option.expanded and selected_option in option.options:
                option.expanded = False
                return idx

    def save_config(self, stdscr):
        """
        Save the current configuration to the output file.

        Args:
            stdscr: Curses window object.
        """
        config_data = self.flatten_options_key_value(self.options)
        with open(self.output_file, 'w') as f:
            json.dump(config_data, f, indent=4)

        if self.custom_save_func:
            self.custom_save_func(config_data)

        stdscr.clear()
        stdscr.addstr(0, 0, "Configuration saved successfully.")
        stdscr.addstr(1, 0, "Press any key to continue.")
        stdscr.refresh()
        stdscr.getch()

    def flatten_options_key_value(self, options):
        """
        Flatten the options into a key-value dictionary.

        Args:
            options (list): List of options.

        Returns:
            dict: Flattened key-value representation of the options.
        """
        config_data = {}
        for option in options:
            if option.option_type == 'group':
                nested_data = self.flatten_options_key_value(option.options)
                if not self.is_option_visible(option):
                    nested_data = {nested_key: None for nested_key in nested_data}
                config_data.update(nested_data)
            else:
                value_to_save = option.choices[option.value] if option.option_type == 'multiple_choice' else option.value or option.default
                config_data[option.name] = None if not self.is_option_visible(option) else value_to_save
        return config_data
