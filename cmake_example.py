from pyconfig import ConfigOption
import pyconfig as pyconfig

import os
import sys

def custom_save(json_data, _):
    with open("output_config.cmake", 'w') as f:
        for key, value in json_data.items():
            if value == None:
                continue
            if isinstance(value, bool):
                f.write(f"SET({key} {'ON' if value else 'OFF'})\n")
            else:
                f.write(f"SET({key} \"{value}\")\n")

def main():
    config = pyconfig.pyconfig(schem_file=["schem.json"], save_func=custom_save)
    config.run()

if __name__ == "__main__":
    main()
