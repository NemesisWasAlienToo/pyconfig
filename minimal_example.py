from pyconfix import ConfigOption
import pyconfix as pyconfix

if __name__ == "__main__":
    config = pyconfix.pyconfix(schem_file=["schem.json"])
    config.run()
