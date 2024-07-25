import json
import library.pyconfig as pyconfig
from library.pyconfig import ConfigOption

# Example custom initialization function
def init_function(config_instance):
    os_specific_option = ConfigOption(
        name='OS',
        option_type='string',
        default="UNIX",
        external=True
    )
    config_instance.options.append(os_specific_option)

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

def main():
    config = pyconfig.pyconfig(config_files=["config.json"], init_func=init_function, save_func=custom_save, expanded=True, show_disabled=True)
    config.run()

if __name__ == "__main__":
    main()
