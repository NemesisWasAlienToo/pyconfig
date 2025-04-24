from pyconfix import pyconfix

if __name__ == "__main__":
    config = pyconfix(schem_file=["schem.json"])
    config.run()
