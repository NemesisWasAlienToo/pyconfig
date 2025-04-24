# pyconfix

> *A single‑file, curses‑powered, ************************************menuconfig‑style************************************ configuration editor for any Python project.*



---

## Why?

Do you need an interactive config menu like Linux **menuconfig**, but without C or a build step? **pyconfix** is forty kilobytes of pure Python you can drop into any repo—no external deps, no compilation. It also spits out JSON or Kconfig‑style header files, so it plugs straight into C/C++, CMake, Conan, Makefiles—anything that can consume a generated file.

---

## Features

- 🗂 **Hierarchical options** – `bool`, `int`, `string`, `multiple_choice`, recursive **groups**.
- 🔀 **Boolean & arithmetic dependencies** with logical operators `&&`, `||`, `!` (keyword forms `and`, `or`, `xor`), comparison/relational operators (`==`, `!=`, `>`, `>=`, `<`, `<=`), arithmetic expressions (`+`, `-`, `*`, `/`, `%`), and bitwise operators (`&`, `|`, `^`, `<<`, `>>`).
- 📦 **Composable schemas** – `"include": [ ... ]` lets you split large configs.
- 🔍 **Instant search** (`/`).
- ⏹ **Abort key** – **Ctrl+A** exits search, input boxes etc.
- 🎚 **Live validation** – options auto‑hide when dependencies fail.
- 💾 **Pluggable save hook** – write JSON, YAML, C headers, env‑files – whatever.
- 💻 **100 % standard library** (Windows users: `pip install windows‑curses`).

---

## Installation

```bash
pip install pyconfix
```

---

## Quick start

Create a tiny launcher script first:

```python
# menu.py
import pyconfix

pyconfix.pyconfix(schem_file=["schem.json"]).run()
```

Then run it:

```bash
python menu.py
```

Press `/` to search, **Enter** to toggle, **s** to save, **q** to quit.

---

## Headless / CI mode

Run the schema parser non‑interactively to dump a JSON config – handy for scripts and pipelines:

```bash
python - <<'PY'
import pyconfix, json
cfg = pyconfix.pyconfix(
    schem_file=["schem.json"],
    output_file="cfg.json",
    config_file="prev.json"
)
cfg.run(graphical=False)
PY
```

## Python API

If you’d rather drive everything from code, import the class:

```python
from pyconfix import pyconfix

cfg = pyconfix(
    schem_file=["main.json", "extras.json"],
    config_file="prev.json",      # load an existing config (optional)
    output_file="final.json",     # where to write when you press "s"
    expanded=True,                 # expand all groups initially
    show_disabled=True             # show options that currently fail deps
)

cfg.run()                # interactive TUI
print(cfg.get("HOST"))   # access a value programmatically
```

Constructor signature for reference:

```python
pyconfix(
    schem_file: list[str],
    config_file: str | None = None,
    output_file: str = "output_config.json",
    save_func: Callable[[dict, list], None] | None = None,
    expanded: bool = False,
    show_disabled: bool = False,
)
```

---

## Key bindings

| Action                  | Key       |
| ----------------------- | --------- |
| Navigate                | ↑  /  ↓   |
| Toggle / edit option    | **Enter** |
| Collapse / expand group | **c**     |
| Search                  | **/**     |
| Save                    | **s**     |
| Show option description | Ctrl+D    |
| Help                    | **h**     |
| Abort search / input    | Ctrl+A    |
| Quit                    | **q**     |

---

## Schema format

```jsonc
{
  "name": "Main Config",
  "options": [
    { "name": "ENABLE_FEATURE_A", "type": "bool", "default": true },

    { "name": "LogLevel",
      "type": "multiple_choice",
      "default": "INFO",
      "choices": ["DEBUG", "INFO", "WARN", "ERROR"],
      "dependencies": "ENABLE_FEATURE_A" },

    { "name": "TIMEOUT",
      "type": "int",
      "default": 10,
      "dependencies": "ENABLE_FEATURE_A && LogLevel==DEBUG" },

    { "name": "Network", "type": "group", "options": [
        { "name": "HOST", "type": "string", "default": "localhost" }
    ]}
  ],
  "include": ["extra_schem.json"]
}
```

### Supported option types

| Type              | Notes                    |
| ----------------- | ------------------------ |
| `bool`            | `true` / `false`         |
| `int`             | any integer              |
| `string`          | unicode string           |
| `multiple_choice` | one value from `choices` |
| `group`           | nests other options      |

### Dependency syntax – cheatsheet

```
!ENABLE_FEATURE_A                     # logical NOT
ENABLE_FEATURE_A && HOST=="dev"       # logical AND + comparison
TIMEOUT>5 || HOST=="localhost"        # logical OR  + relational
COUNT+5 > MAX_VALUE                   # addition + relational
SIZE-1 >= MIN_SIZE                    # subtraction + comparison
VALUE*2 == LIMIT                      # multiplication + equality
RATIO/3 < 1                           # division + relational
SIZE%4==0                             # modulus check
POWER**2 <= LIMIT                     # exponentiation + relational
BITS & 0xFF == 0xAA                   # bitwise AND + equality
FLAGS | FLAG_VERBOSE                  # bitwise OR
MASK ^ 0b1010                         # bitwise XOR
VALUE<<2 > 1024                       # left shift + relational
VALUE>>1 == 0                         # right shift + equality
```

---

## Advanced usage

```python
import json, pyconfix

def save_as_header(cfg, _):
    with open("config.h", "w") as f:
        for k, v in cfg.items():
            f.write(f"#define {k} {v}\n")

pyconfix.pyconfix(
    schem_file=["schem.json", "extras.json"],
    output_file="settings.json",
    save_func=save_as_header
).run()
```

---

## Conan integration example

After you have saved a JSON config with **pyconfix** (e.g. `settings.json`), a Conan recipe can read that file to enable/disable features and tweak package options at build time.

```python
# conanfile.py
from conan import ConanFile
import os, json

# Load the JSON produced by pyconfix at *import* time so we can
# populate default_options immediately (Conan expects a plain dict).
_cfg = {}
try:
    with open(os.getenv("CFG", "settings.json")) as f:
        _cfg = json.load(f)
except FileNotFoundError:
    # Fall back to built‑ins if the file isn't around yet (first run).
    pass

class MyProject(ConanFile):
    name = "myproject"
    version = "1.0"

    # Declare the build‑time options your project cares about
    options = {
        "feature_a": [True, False],
        "log_level": ["DEBUG", "INFO", "WARN", "ERROR"],
    }
    # Pull the defaults straight from the JSON file
    default_options = {
        "feature_a": bool(_cfg.get("ENABLE_FEATURE_A", False)),
        "log_level": _cfg.get("LogLevel", "INFO"),
    }
```

Call it with:

```bash
python pyconfix.py              # produce settings.json
CFG=settings.json conan install .
```

---

## Roadmap

- Add unit tests + GitHub Actions CI
- Cache dependency evaluation for massive configs

Contributions are welcome – fork, hack, send PRs! \:rocket:

---

© 2025 Nemesis – MIT License

