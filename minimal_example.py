from pyconfig import ConfigOption
import pyconfig as pyconfig

if __name__ == "__main__":
    config = pyconfig.pyconfig(schem_file=["schem.json"])
    config.run()
