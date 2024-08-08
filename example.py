from library.pyconfig import ConfigOption
import library.pyconfig as pyconfig

import curses
import subprocess
import threading
import fcntl
import os
import sys

def execute_command(stdscr):
    y = 0
    max_y, _ = stdscr.getmaxyx()
    
    # Clear screen and set up scrolling
    stdscr.clear()
    stdscr.scrollok(True)

    # Command to be executed
    command = "ping google.com"  # Replace with your long-running command

    def read_output(process, stdscr, stop_event):
        nonlocal y
        # Set stdout to non-blocking mode
        flags = fcntl.fcntl(process.stdout, fcntl.F_GETFL)
        fcntl.fcntl(process.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        while not stop_event.is_set():
            max_y, _ = stdscr.getmaxyx()  # Get the window's dimensions

            try:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    try:
                        # Print the output above the bottom line
                        stdscr.addstr(y, 0, output.strip())
                        stdscr.clrtoeol()  # Clear the rest of the line
                        y += 1
                        if y >= max_y:  # Prevent scrolling from overwriting the prompt
                            stdscr.scroll(1)
                            y = max_y - 1  # Keep one line above the prompt for new output
                    except curses.error:
                        pass

                # Always draw the prompt at the bottom
                stdscr.addstr(max_y - 1, 0, "Press 'q' to terminate")
                stdscr.clrtoeol()  # Ensure the line is cleared before writing
                stdscr.refresh()
            except IOError:
                pass  # Ignore empty reads

    # Event to signal when to stop reading output
    stop_event = threading.Event()
    
    # Start the command with stdout being piped
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Start a separate thread to read the output
    output_thread = threading.Thread(target=read_output, args=(process, stdscr, stop_event))
    output_thread.start()
    
    # Wait for user input to cancel
    while process.poll() is None:
        key = stdscr.getch()
        if key == ord('q'):
            stop_event.set()
            process.terminate()
            break

    # Wait for the output thread to finish
    output_thread.join()

# Example custom initialization function
def init_function(config_instance):
    config_instance.options.append(
        ConfigOption(
            name='OS',
            option_type='string',
            default="UNIX",
            external=True
    ))
    config_instance.options.append(
        ConfigOption(
            name='compile',
            option_type="action",
            description="Compiles the code",
            dependencies=["ENABLE_FEATURE_A"],
            default=execute_command
    ))

def custom_save(json_data, _):
    with open("output_defconfig", 'w') as f:
        for key, value in json_data.items():
            if value == None or (isinstance(value, bool) and value == False):
                f.write(f"# {key} is not set\n")
            else:
                if isinstance(value, str):
                    f.write(f"{key}=\"{value}\"\n")
                else:
                    f.write(f"{key}={value if value != True else 'y'}\n")
    with open("output_config.cmake", 'w') as f:
        for key, value in json_data.items():
            if value == None or (isinstance(value, bool) and value == False):
                continue

            if isinstance(value, str):
                f.write(f"SET({key} \"{value}\")\n")
            else:
                f.write(f"SET({key} {value if value != True else 'True'})\n")

def main():
    load_file:str = None
    if len(sys.argv) > 1:
        load_file = sys.argv[1] if os.path.exists(sys.argv[1]) else None
    config = pyconfig.pyconfig(schem_file=["schem.json"], config_file=load_file, init_func=init_function, save_func=custom_save, expanded=True, show_disabled=True)
    config.run()

if __name__ == "__main__":
    main()
