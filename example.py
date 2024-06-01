import json
import library.pyconfig as pyconfig
from library.pyconfig import ConfigOption

# Example custom initialization function
def init_function(config_instance):
    os_specific_option = ConfigOption(
        name='UNIX',
        option_type='bool',
        default=True
    )
    config_instance.options.append(os_specific_option)

def main():
    def custom_save(config_data):
        with open("custom_output_config.json", 'w') as f:
            json.dump(config_data, f, indent=4)
        print("Custom config saved")

    config = pyconfig.pyconfig(config_files=["config.json"], custom_save_func=custom_save, expanded=True, show_disabled=True, init_func=init_function)
    config.run()

if __name__ == "__main__":
    main()
