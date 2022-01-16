import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "flipside_toolchain",
    version = "0.0.1a",
    author = "lambdadelta.ust",
    description = ("Toolchain for FlipsideCrypto Analytic with Python"),
    license = "MIT",
    keywords = "tools",
    long_description=read('README.txt'),
    classifiers=[
        "License :: MIT License",
    ],
    install_requires=[
        'pandas >= 1.1.0',
        'bech32 == 1.2.0',
        'terra_sdk',
        'tqdm'
    ],
    package_dir={'': 'src'},
    packages=find_packages(where='src', include=['flipside_toolchain', 'flipside_toolchain.*']),
    include_package_data=True
)