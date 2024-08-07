import json
import curses
import curses.textpad
import os
import re
import textwrap

class ConfigOption:
    def __init__(self, name, option_type, default, external = None, data = None, dependencies=None, options=None, choices=None, expanded=False):
        self.name = name
        self.option_type = option_type
        self.value = default
        self.default = default
        # External options cannot be modified by the user
        self.external = external or False
        self.data = data
        self.dependencies = dependencies or []
        self.options = options or []
        self.choices = choices or []
        self.expanded = expanded

    def to_dict(self):
        return {
            'name': self.name,
            'type': self.option_type,
            'default': self.default,
            'external': self.external,
            'data': self.data,
            'dependencies': self.dependencies,
            'options': [opt.to_dict() for opt in self.options],
            'choices': self.choices
        }
    
class pyconfig:
    def __init__(self, config_files, output_file="output_config.json", save_func=None, init_func=None, expanded=False, show_disabled=False):
        self.config_files = config_files
        self.output_file = output_file
        self.save_func = save_func
        self.init_func = init_func
        self.show_disabled = show_disabled
        self.expanded = expanded
        self.options = []
        self.config_name = ""
        self.load_config()
        self.apply_saved_config()

        self.save_key = ord('s')
        self.collapse_key = ord('c')
        self.quite_key = ord('q')
        self.search_key = ord('/')
        self.help_key = ord('h')
        self.exit_search_key = curses.KEY_F1
        self.force_enable_key = curses.KEY_F2

    def show_help(self, stdscr):
        help_text = [
            "Help Page",
            "",
            "Keybindings:",
            "  Arrow Up/Down: Navigate",
            "  Enter: Select/Toggle option",
            "  s: Save configuration",
            "  q: Quit",
            "  c: Collapse/Expand group",
            "  /: Search",
            "  h: Show this help page",
            "  F1: Exit search",
            "  F2: To forece enable (if disable item is visible)",
            "",
            "How it works:",
            "  - Use the arrow keys to navigate through the options.",
            "  - Press Enter to select or toggle an option.",
            "  - Options that depend on other options will be shown or hidden based on their dependencies.",
            "  - Use the search function to quickly find options by name.",
            "  - Press 'c' to collapse or expand groups of options.",
            ""
        ]

        start_index = 0
        while True:
            stdscr.clear()
            # stdscr.border(0)  # Draw the border
            max_y, max_x = stdscr.getmaxyx()

            # stdscr.addstr(0, 2, " Help Page ")
            if max_y > 2:
                stdscr.addstr(max_y - 2, 2, "Press 'q' to return to the menu or UP/DOWN to scroll")

            display_limit = max_y - 3
            for idx, line in enumerate(help_text[start_index:start_index + display_limit]):
                stdscr.addstr(idx + 1, 2, line)
            
            stdscr.refresh()
            key = stdscr.getch()

            if key == curses.KEY_UP and start_index > 0:
                start_index -= 1
            elif key == curses.KEY_DOWN and start_index < len(help_text) - display_limit:
                start_index += 1
            elif key == curses.KEY_RESIZE:
                # Adjust the display limit on terminal resize
                max_y, max_x = stdscr.getmaxyx()
                display_limit = max_y - 2
            elif key == ord('q'):
                break

    def load_config(self):
        # Run the custom initialization function if provided
        if self.init_func:
            self.init_func(self)

        for config_file in self.config_files:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                self.config_name = config_data.get('name', 'Configuration')
                self.parse_options(config_data['options'], self.options)
                for include_file in config_data.get('include', []):
                    with open(include_file, 'r') as f:
                        extra_config_data = json.load(f)
                        self.parse_options(extra_config_data['options'], self.options)

    def parse_options(self, options_data, parent_list, group_dependencies = []):
        for option_data in options_data:
            option = ConfigOption(
                name=option_data['name'],
                option_type=option_data['type'],
                default=option_data.get('default'),
                dependencies=option_data.get('dependencies', []) + group_dependencies,
                choices=option_data.get('choices', []),
                expanded=self.expanded,
                options=[]
            )
            if option.option_type == 'group' and 'options' in option_data:
                self.parse_options(option_data['options'], option.options, option.dependencies)
                [opt.dependencies.extend(group_dependencies) for opt in option.options]
            elif option.option_type == 'multiple_choice':
                option.value = option.choices.index(option.default)
            parent_list.append(option)

    def apply_saved_config(self):
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r') as f:
                saved_config = json.load(f)
                self.apply_config_to_options(self.options, saved_config)

    def apply_config_to_options(self, options, saved_config):
        for option in options:
            if option.option_type == 'group':
                self.apply_config_to_options(option.options, saved_config)
            elif option.name in saved_config:
                value = saved_config[option.name]
                option.value = saved_config[option.name] if option.option_type != 'multiple_choice' else option.choices.index(value if value else option.default)
        self.reset_hidden_dependent_options(self.options)

    def reset_hidden_dependent_options(self, options):
        for option in options:
            if option.option_type == 'group':
                self.reset_hidden_dependent_options(option.options)
            elif not self.is_option_available(option):
                option.value = option.default if option.option_type != 'multiple_choice' else option.choices.index(option.default)

    def is_option_available(self, option):
        return all(self.is_dependency_met(dep, self.options) for dep in option.dependencies)
    
    def option_meets_dependency(self, option, dependency_string):
        if option.option_type == 'group':
            return False
        elif dependency_string.startswith('!'):
            key = dependency_string[1:]
            # return (option.name == key and option.value == False)
            return (option.name == key and not option.value)
        elif option.value == None:
            return False
        elif match := re.match(r'^([^=]+)=([^=]+)$', dependency_string):
            key, value = match.groups()
            values = [name.strip() for name in value.split(',')]
            return ((option.name == key and option.value in values) or 
                   (option.option_type == 'multiple_choice' and option.choices[option.value] in values) or
                   (option.option_type == 'int' and str(option.value) in values) or
                   (option.option_type == 'string' and option.value in values))
        return (option.name == dependency_string and option.value)

    def is_dependency_met(self, dependency_string, options):
        return any(self.option_meets_dependency(opt, dependency_string) for opt in options)

    def flatten_options(self, options, depth=0):
        flat_options = []
        for option in options:
            if not self.is_option_available(option):
                if option.option_type != 'group':
                    option.value = None
                if not self.show_disabled:
                    continue
            else:
                if option.value == None:
                    option.value = option.choices.index(option.default) if option.option_type == 'multiple_choice' else option.default
            flat_options.append((option, depth))
            if option.option_type == 'group' and option.expanded:
                flat_options.extend(self.flatten_options(option.options, depth + 1))
        return flat_options

    def search_options(self, options, query, depth=0):
        flat_options = []
        for option in options:
            if self.show_disabled or self.is_option_available(option):
                if option.option_type == 'group':
                    nested_options = self.search_options(option.options, query, depth + 1)
                    if nested_options:
                        option.expanded = True  # Ensure the group is expanded in search mode
                        flat_options.append((option, depth))
                        flat_options.extend(nested_options)
                elif query.lower() in option.name.lower():
                    flat_options.append((option, depth))
        return flat_options
    
    def prompt(self, stdscr, message):
        message = f"{message} (Press any key)"

        while True:
            stdscr.clear()
            curses.curs_set(0)  # Hide the cursor
            max_y, max_x = stdscr.getmaxyx()
            wrapped_text = textwrap.wrap(message, max_x - 4)
            question_lines = len(wrapped_text)
            question_start_y = max_y // 2 - question_lines // 2 - 1
            for i, line in enumerate(wrapped_text):
                stdscr.addstr(question_start_y + i, (max_x - len(line)) // 2, line)

            stdscr.refresh()
            key = stdscr.getch()

            if key != curses.KEY_RESIZE:
                break
    
    def message_box(self, stdscr, message):
        message = f"{message} (Press 'q' to cancel.)"
        yes_option = "[ Yes ]"
        no_option = "[ No ]"
        current_option = 0  # 0 for Yes, 1 for No

        while True:
            stdscr.clear()
            curses.curs_set(0)  # Hide the cursor
            max_y, max_x = stdscr.getmaxyx()
            wrapped_text = textwrap.wrap(message, max_x - 4)
            # Calculate positions
            question_y = max_y // 2 - 1
            yes_y = question_y + 2
            yes_x = (max_x // 2) - len(yes_option) - 2
            no_y = yes_y
            no_x = (max_x // 2) + 2
            question_lines = len(wrapped_text)
            question_start_y = max_y // 2 - question_lines // 2 - 1
            for i, line in enumerate(wrapped_text):
                stdscr.addstr(question_start_y + i, (max_x - len(line)) // 2, line)
            
            if max_y > 3:
                # Display Yes/No options
                if current_option == 0:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(yes_y, yes_x, yes_option)
                    stdscr.attroff(curses.color_pair(1))
                    stdscr.addstr(no_y, no_x, no_option)
                else:
                    stdscr.addstr(yes_y, yes_x, yes_option)
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(no_y, no_x, no_option)
                    stdscr.attroff(curses.color_pair(1))

            stdscr.refresh()
            key = stdscr.getch()

            if key == curses.KEY_LEFT or key == curses.KEY_RIGHT:
                current_option = 1 - current_option  # Toggle between 0 and 1
            elif key in (curses.KEY_ENTER, 10, 13):
                return current_option == 0  # True for Yes, False for No
            elif key == ord('q'):
                return None

    def display_options(self, stdscr, flat_options, start_index, current_row, search_mode):
        max_y, max_x = stdscr.getmaxyx()
        display_limit = max_y - 4 if not search_mode else max_y - 6
        for idx in range(start_index, min(start_index + display_limit, len(flat_options))):
            option, depth = flat_options[idx]
            indicator = "[+]" if option.option_type == 'group' and not option.expanded else "[-]" if option.option_type == 'group' else ""
            name = f"{indicator} {option.name}" if option.option_type == 'group' else option.name
            value = ""
            if option.external:
                value = f"{option.value} [external]"
            elif option.value == None and option.option_type != 'group':
                value = "[disabled]"
            elif option.option_type == 'multiple_choice':
                value = option.choices[option.value]
            elif option.option_type == 'bool':
                value = "True" if option.value else "False"
            elif option.option_type in ['int', 'string']:
                value = str(option.value)

            display_text = f"{name}: {value}" if value != None else name
            if len(display_text) > max_x - 2:
                display_text = display_text[:max_x - 5] + "..."
            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
            stdscr.addstr(2 + idx - start_index, 2 + depth * 2, display_text)
            if idx == current_row:
                stdscr.attroff(curses.color_pair(1))

    def run(self):
        curses.wrapper(self.menu_loop)

    def menu_loop(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        current_row = 0
        search_mode, search_query = False, ""
        start_index = 0

        while True:
            stdscr.clear()
            stdscr.border(0)
            stdscr.addstr(0, 2, f" {self.config_name} ")
            max_y, max_x = stdscr.getmaxyx()
            if not search_mode and max_y > 2:
                info = "Press 'q' to Exit, 's' to Save, 'c' to Collapse Group, '/' to Search" + ", 'h' for more" if self.show_disabled else ""
                info = info[:max_x - 5]
                stdscr.addstr(max_y - 2, 2, info)

            if search_mode:
                flat_options = self.search_options(self.options, search_query)
            else:
                flat_options = self.flatten_options(self.options)

            # Adjust current_row and start_index to prevent out-of-range errors
            if current_row >= len(flat_options):
                current_row = len(flat_options) - 1
            if current_row < 0:
                current_row = 0
            if current_row < start_index:
                start_index = current_row
            elif current_row >= start_index + (max_y - 6 if search_mode else max_y - 4):
                start_index = current_row - (max_y - 7 if search_mode else max_y - 5)
            
            self.display_options(stdscr, flat_options, start_index, current_row, search_mode)

            if search_mode:
                if max_y > 3:
                    stdscr.addstr(max_y - 3, 2, f"Search: {search_query}")
                if max_y > 2:
                    stdscr.addstr(max_y - 2, 2, "Press F1 to exit search")

            stdscr.refresh()
            key = stdscr.getch()

            if key == curses.KEY_RESIZE:
                stdscr.clear()
                max_y, max_x = stdscr.getmaxyx()
                continue

            if search_mode:
                if key in (curses.KEY_BACKSPACE, 127):
                    search_query = search_query[:-1]
                elif key == self.exit_search_key:
                    stdscr.timeout(100)
                    if stdscr.getch() == -1:
                        search_mode, search_query = False, ""
                    stdscr.timeout(-1)
                elif 32 <= key <= 126:
                    search_query += chr(key)
                elif key in (curses.KEY_UP, curses.KEY_DOWN):
                    if key == curses.KEY_UP and current_row > 0:
                        current_row -= 1
                    elif key == curses.KEY_DOWN and current_row < len(flat_options) - 1:
                        current_row += 1
                elif key in (curses.KEY_ENTER, 10, 13):
                    self.handle_enter(flat_options, current_row, stdscr, search_mode)
                elif key == self.force_enable_key:
                    self.handle_force_enable(flat_options, current_row, stdscr, search_mode)
            else:
                if key in (curses.KEY_UP, curses.KEY_DOWN):
                    if key == curses.KEY_UP and current_row > 0:
                        current_row -= 1
                        if current_row < start_index:
                            start_index -= 1
                    elif key == curses.KEY_DOWN and current_row < len(flat_options) - 1:
                        current_row += 1
                        if current_row >= start_index + max_y - 4:
                            start_index += 1
                elif key in (curses.KEY_ENTER, 10, 13):
                    self.handle_enter(flat_options, current_row, stdscr, search_mode)
                elif key == self.save_key:
                    self.save_config(stdscr)
                elif key == self.quite_key:
                    break
                elif key == self.collapse_key:
                    current_row = self.collapse_current_group(flat_options, current_row, search_mode)
                elif key == self.force_enable_key:
                    self.handle_force_enable(flat_options, current_row, stdscr, search_mode)
                elif key == self.search_key:
                    search_mode, search_query, current_row = True, "", 0
                elif key == self.help_key:
                    self.show_help(stdscr)

    def handle_force_enable(self, flat_options, row, stdscr, search_mode):
        if not flat_options:
            return
        selected_option, _ = flat_options[row]
        # External options cannot be modified by the user
        if self.is_externally_restricted(selected_option):
            self.prompt(stdscr, "This item has external dependencies which cannot be modified")
            return
        if selected_option.value != None or selected_option.option_type == 'group':
            return
        self.force_enable_option(selected_option)

    def handle_enter(self, flat_options, row, stdscr, search_mode):
        if not flat_options:
            return
        
        selected_option, _ = flat_options[row]

        if selected_option.value == None and selected_option.option_type != 'group':
            return
        
        # External options cannot be modified by the user
        if selected_option.external:
            return
        
        if selected_option.option_type == 'bool':
            selected_option.value = not selected_option.value
        elif selected_option.option_type == 'group':
            if not search_mode:
                selected_option.expanded = not selected_option.expanded
        elif selected_option.option_type in ['int', 'string']:
            self.edit_option(stdscr, selected_option)
        elif selected_option.option_type == 'multiple_choice':
            self.edit_multiple_choice_option(stdscr, selected_option)

        self.reset_dependent_options(selected_option, self.options)

    def edit_option(self, stdscr, option):
        if option.value == None:
            return
        
        original_value = option.value
        curses.curs_set(1)
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        stdscr.addstr(0, 0, f"Editing {option.name} (current value: {option.value}): ")
        stdscr.addstr(1, 0, "Press ENTER to save, ESC or 'q' to cancel.")
        editwin = curses.newwin(3, max_x - 2, 2, 1)
        curses.textpad.rectangle(stdscr, 1, 0, 4, max_x - 1)
        stdscr.addstr(max_y - 2, 2, " Press F10 to Cancel ")
        stdscr.refresh()
        box = curses.textpad.Textbox(editwin, insert_mode=True)

        def validate_input(ch):
            if ch == curses.KEY_F10:
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
        curses.curs_set(0)
        current_choice = option.value if option.value is not None else 0
        original_choice = option.value
        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Editing {option.name} (current choice: {option.choices[current_choice]}): ")
            stdscr.addstr(1, 0, "Use UP/DOWN to change choice, ENTER to save, ESC or 'q' to cancel.")
            stdscr.addstr(curses.LINES - 2, 2, " Press F10 to Cancel ")
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
            elif key in (27, curses.KEY_F10):
                option.value = original_choice
                break

    def collapse_current_group(self, flat_options, current_row, search_mode):
        selected_option, _ = flat_options[current_row]
        if selected_option.option_type == 'group':
            selected_option.expanded = not selected_option.expanded
            if search_mode:
                # Collapse all children in search mode to reflect changes
                for option, _ in flat_options:
                    if option in selected_option.options:
                        option.expanded = selected_option.expanded
            return current_row
        for idx, (option, depth) in enumerate(flat_options):
            if option.option_type == 'group' and option.expanded and selected_option in option.options:
                option.expanded = False
                return idx
            
        return current_row

    def save_config(self, stdscr):
        config_data = self.flatten_options_key_value(self.options)
        with open(self.output_file, 'w') as f:
            json.dump(config_data, f, indent=4)

        if self.save_func:
            self.save_func(config_data, self.options)

        stdscr.clear()
        stdscr.addstr(0, 0, "Configuration saved successfully.")
        stdscr.addstr(1, 0, "Press any key to continue.")
        stdscr.refresh()
        stdscr.getch()

    def flatten_options_key_value(self, options):
        config_data = {}
        for option in options:
            if option.option_type == 'group':
                nested_data = self.flatten_options_key_value(option.options)
                if not self.is_option_available(option):
                    nested_data = {nested_key: None for nested_key in nested_data}
                config_data.update(nested_data)
            else:
                value_to_save = None if option.value == None else option.choices[option.value] if option.option_type == 'multiple_choice' else (option.value if option.value != None else option.default)
                config_data[option.name] = None if not self.is_option_available(option) else value_to_save
        return config_data

    def reset_dependent_options(self, option, options):
        for opt in options:
            if any(self.option_meets_dependency(option, dep) for dep in opt.dependencies):
                if self.is_option_available(opt) and opt.value == None:
                    opt.value = opt.default if opt.option_type != 'multiple_choice' else opt.choices.index(opt.default)
                    self.reset_dependent_options(opt, self.options)
                if opt.option_type == 'group':
                    self.reset_dependent_options(option, opt.options)

    def find_option(self, name, options = None):
        for opt in options:
            if opt.name == name:
                return opt
        return None
        
    def is_externally_restricted(self, option):
        if option.external:
            return True
        
        for dependency_string in option.dependencies:
            key = ""
            if dependency_string.startswith('!'):
                key == dependency_string[1:]
            elif match := re.match(r'^([^=]+)=([^=]+)$', dependency_string):
                key, _ = match.groups()
            else:
                key = dependency_string

            opt = self.find_option(key, self.options)
            if opt == None:
                return False

            if self.is_externally_restricted(opt):
                return True
        return False

    def option_in_dependency(self, option, dependency_string):
        if option.option_type == 'group':
            return False
        if dependency_string.startswith('!'):
            return option.name == dependency_string[1:]
        elif match := re.match(r'^([^=]+)=([^=]+)$', dependency_string):
            key, _ = match.groups()
            return option.name == key
        return option.name == dependency_string
    
    def extract_force_enable_value_if_applicable(self, option, dependency_string):
        if option.option_type == 'group':
            return
        if dependency_string.startswith('!'):
            key = dependency_string[1:]
            if option.name == key and option.value:
                return False
            return option.value
        elif match := re.match(r'^([^=]+)=([^=]+)$', dependency_string):
            key, value = match.groups()
            if option.name == key:
                if option.option_type == 'multiple_choice':
                    return option.value if option.choices[option.value] in value else option.choices.index(option.defalut)
                elif str(option.value) not in value:
                    return [name.strip() for name in value.split(',')][0]
                return option.value
        return True if option.name == dependency_string else None

    def force_enable_option(self, option, set_value = None):
        if option.option_type == 'bool':
            option.value = set_value if set_value != None else True
        elif option.option_type == 'multiple_choice':
            option.value = set_value if set_value != None else option.choices.index(option.default)
        else:
            option.value = set_value if set_value != None else option.default
        
        self.reset_dependent_options(option, self.options)

        for opt in self.options:
            for dep in option.dependencies:
                if self.option_in_dependency(opt, dep):
                    extracted_value = self.extract_force_enable_value_if_applicable(opt, dep)
                    self.force_enable_option(opt, extracted_value)
