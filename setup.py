from setuptools import setup

setup(
    name="pyconfix",
    version="0.2.0",
    description="A simple feature managment tool library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Nemesis",
    author_email="nemesiswasalientoo@proton.me",
    url="https://github.com/NemesisWasAlienToo/pyconfix",
    py_modules=["pyconfix"],
    python_requires=">=3.7",
    license="MIT",
    install_requires=[
        "windows-curses;platform_system=='Windows'"
    ],
)