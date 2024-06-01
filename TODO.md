With this json the dependency incompatibility will cause problem:

{
    "name": "Main Config",
    "options": [
        {
            "name": "ENABLE_FEATURE_A",
            "type": "bool",
            "default": true,
            "dependencies": []
        },
        {
            "name": "ENABLE_FEATURE_B",
            "type": "bool",
            "default": 0
        },
        {
            "name": "LogLevel",
            "type": "multiple_choice",
            "default": "DEBUG",
            "choices": ["DEBUG", "INFO", "WARN", "ERROR"],
            "dependencies": [
                "ENABLE_FEATURE_A"
            ]
        },
        {
            "name": "INTERMEDIATE_OPTION",
            "type": "bool",
            "default": true,
            "dependencies": [
                "ENABLE_FEATURE_A"
            ]
        },
        {
            "name": "Depens on A and B",
            "type": "int",
            "default": 0,
            "dependencies": [
                "ENABLE_FEATURE_A",
                "ENABLE_FEATURE_B",
                "LogLevel=DEBUG,INFO",
                "!INTERMEDIATE_OPTION",
                "DOMAIN_ADDRESS=localhost,otherhost"
            ]
        },
        {
            "name": "Feature A Level 2",
            "type": "int",
            "default": 0,
            "dependencies": [
                "ENABLE_FEATURE_A"
            ]
        },
        {
            "name": "Feature A Level 3",
            "type": "int",
            "default": 0,
            "dependencies": [
                "ENABLE_FEATURE_A"
            ]
        },
        {
            "name": "Feature A Level 4",
            "type": "int",
            "default": 0,
            "dependencies": [
                "ENABLE_FEATURE_A"
            ]
        },
        {
            "name": "DOMAIN_ADDRESS",
            "type": "string",
            "default": "localhost",
            "dependencies": [
                "ENABLE_FEATURE_A"
            ]
        },
        {
            "name": "Group 1",
            "type": "group",
            "default": [],
            "dependencies": [
                "ENABLE_FEATURE_A"
            ],
            "options": [
                {
                    "name": "Enable Sub Feature B",
                    "type": "bool",
                    "default": false
                },
                {
                    "name": "Group 2",
                    "type": "group",
                    "default": [],
                    "options": [
                        {
                            "name": "Enable Sub Feature C",
                            "type": "bool",
                            "default": false
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