
# pyconfix

pyconfix is a Python-based configuration management tool with a text-based user interface built using curses. It allows you to manage complex configurations, including nested groups and dependencies between options. This library aims to provide a more user-friendly, configurable, and expandable alternative to menuconfig.

## Features

- Load and save configurations from JSON files
- Support for multiple option types: boolean, integer, string, multiple choice, and groups
- Search functionality to quickly find and modify options
- Dependencies between options to control visibility and availability

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/NemesisWasAlienToo/pyconfix.git
cd pyconfix
```

Install the required dependencies (if any). This project uses standard libraries, so no additional dependencies are required.

## Usage

Run the pyconfix by executing the `pyconfix.py` script:

```bash
python example.py
```

## JSON Configuration Example

The configuration is defined in JSON format. Here is an example of a configuration file (`config.json`):

```json
{
    "name": "Main Config",
    "options": [
        {
            "name": "Enable Feature A",
            "type": "bool",
            "default": true,
            "dependencies": []
        },
        {
            "name": "LogLevel",
            "type": "multiple_choice",
            "default": 1,
            "choices": ["DEBUG", "INFO", "WARN", "ERROR"],
            "dependencies": [
                "Enable Feature A"
            ]
        },
        {
            "name": "Feature A Level",
            "type": "int",
            "default": 0,
            "dependencies": [
                "Enable Feature A"
            ]
        },
        {
            "name": "Feature S Level",
            "type": "string",
            "default": "Hello",
            "dependencies": [
                "Enable Feature A"
            ]
        },
        {
            "name": "Group 1",
            "type": "group",
            "default": [],
            "dependencies": [
                "Enable Feature A"
            ],
            "options": [
                {
                    "name": "Enable Sub Feature B",
                    "type": "bool",
                    "default": false,
                    "dependencies": []
                },
                {
                    "name": "Group 2",
                    "type": "group",
                    "default": [],
                    "dependencies": [],
                    "options": [
                        {
                            "name": "Enable Sub Feature C",
                            "type": "bool",
                            "default": false,
                            "dependencies": []
                        }
                    ]
                }
            ]
        }
    ],
    "include": [
        "extra_config.json"
    ]
}
```

### Configuration Fields Breakdown

1. **name**: The name of the configuration.
    ```json
    "name": "Main Config"
    ```

2. **options**: A list of configuration options.
    - **name**: The name of the option.
    - **type**: The type of the option (`bool`, `int`, `string`, `multiple_choice`, `group`).
    - **default**: The default value of the option.
    - **dependencies**: A list of dependencies. The option is visible and available only if all dependencies are met.
    - **choices**: For `multiple_choice` options, a list of possible choices.
    - **options**: For `group` options, a list of sub-options.

    Example:
    ```json
    {
        "name": "Enable Feature A",
        "type": "bool",
        "default": true,
        "dependencies": []
    }
    ```

3. **include**: A list of additional JSON files to include.
    ```json
    "include": [
        "extra_config.json"
    ]
    ```

### Adding New Options

To add new options, you can define them in the `options` list within the configuration JSON file. Here are the types of options you can add:

#### Boolean Option
Represents a boolean value (true/false).
```json
{
    "name": "Enable Feature X",
    "type": "bool",
    "default": false,
    "dependencies": []
}
```

#### Integer Option
Represents an integer value.
```json
{
    "name": "Feature X Level",
    "type": "int",
    "default": 0,
    "dependencies": []
}
```

#### String Option
Represents a string value.
```json
{
    "name": "Feature X Name",
    "type": "string",
    "default": "Default Name",
    "dependencies": []
}
```

#### Multiple Choice Option
Represents a choice from a predefined list of values.
```json
{
    "name": "LogLevel",
    "type": "multiple_choice",
    "default": 1,
    "choices": ["DEBUG", "INFO", "WARN", "ERROR"],
    "dependencies": []
}
```

#### Group Option
Represents a group of nested options.
```json
{
    "name": "Group X",
    "type": "group",
    "default": [],
    "dependencies": [],
    "options": [
        {
            "name": "Enable Sub Feature Y",
            "type": "bool",
            "default": false,
            "dependencies": []
        }
    ]
}
```

## Example Code

Here's an example of how to define a custom save function and run the pyconfix:

```python
import json
import library.pyconfix as pyconfix

def main():
    def custom_save(config_data):
        with open("custom_output_config.json", 'w') as f:
            json.dump(config_data, f, indent=4)
        print("Custom config saved")

    config = pyconfix.pyconfix(config_files=["config.json"], custom_save_func=custom_save)
    config.run()

if __name__ == "__main__":
    main()
```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.