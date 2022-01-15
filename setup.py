import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "Flipside Toolchain",
    version = "0.0.1a",
    author = "lambdadelta.ust",
    description = ("Toolchain for FlipsideCrypto Analytic with Python"),
    license = "MIT",
    keywords = "tools",
    packages=['flipside_toolchain'],
    long_description=read('README.txt'),
    classifiers=[
        "License :: MIT License",
    ],
    install_requires=[
        'pandas >= 1.3.5',
        'bech32 == 1.2.0'
    ]
)