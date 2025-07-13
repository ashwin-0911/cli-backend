from setuptools import setup, find_packages

setup(
    name="qgjob",
    version="0.1",
    packages=find_packages(include=["cli", "cli.*"]),
    install_requires=["requests"],
    entry_points={
        "console_scripts": [
            "qgjob = cli.main:main"
        ]
    }
)