from pyconfig import ConfigOption
import pyconfig as pyconfig

import curses
import subprocess
import threading
import fcntl
import os
import sys

def execute_command(stdscr):
    stdscr.clear()
    curses.endwin()
    print("\033[?1049l", end="")

    # Command to run
    command = "ping google.com"  # Replace with your long-running command

    def read_output(process, stdscr, stop_event):
        curses.endwin()
        # Set stdout to non-blocking mode
        flags = fcntl.fcntl(process.stdout, fcntl.F_GETFL)
        fcntl.fcntl(process.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        while not stop_event.is_set():
            try:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    print(f"{output}", end="\r")
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

def custom_save(json_data, _):
    with open("output_defconfig", 'w') as f:
        for key, value in json_data.items():
            if value == None or (isinstance(value, bool) and value == False):
                f.write(f"# {key} is not set\n")
            else:
                if isinstance(value, str):
                    f.write(f"CONFIG_{key}=\"{value}\"\n")
                else:
                    f.write(f"CONFIG_{key}={value if value != True else 'y'}\n")
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
    
    config = pyconfig.pyconfig(schem_file=["schem.json"], config_file=load_file, save_func=custom_save, expanded=True, show_disabled=True)

    config.options.append(
        ConfigOption(
            name='OS',
            option_type='string',
            default="UNIX",
            external=True
    ))

    config.options.append(
        ConfigOption(
            name='compile',
            option_type="action",
            description="Compiles the code",
            dependencies="ENABLE_FEATURE_A",
            default=execute_command
    ))
    
    config.run()

if __name__ == "__main__":
    main()
