#!/usr/bin/env python

from setuptools import setup, find_packages


with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="pubproxpy",
    version="0.1.8",
    description="A public proxy list provider using the pubproxy.com API",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="LovecraftianHorror",
    author_email="LovecraftianHorror@pm.me",
    url="https://github.com/LovecraftianHorror/pubproxpy",
    packages=find_packages(exclude=("tests", "docs")),
    install_requires=["requests"],
    classifiers=["Programming Language :: Python :: 3.6"],
    keywords=["proxy", "public proxy", "pubproxy api", "proxy api" "pubproxy"],
)
