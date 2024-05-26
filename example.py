import json
import library.pyconfig as pyconfig

def main():
    def custom_save(config_data):
        with open("custom_output_config.json", 'w') as f:
            json.dump(config_data, f, indent=4)
        print("Custom config saved")

    config_manager = pyconfig.pyconfig(config_files=["config.json"], custom_save_func=custom_save)
    config_manager.run()

if __name__ == "__main__":
    main()
