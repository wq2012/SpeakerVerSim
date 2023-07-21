"""Setup script for the package."""

import setuptools

VERSION = "0.1.2"
DESCRIPTION = (
    "Simulation framework for version control strategies "
    "of speaker recognition systems.")

with open("README.md", "r") as file_object:
    LONG_DESCRIPTION = file_object.read()

setuptools.setup(
    name="SpeakerVerSim",
    version=VERSION,
    author="Quan Wang",
    author_email="quanw@google.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/wq2012/SpeakerVerSim",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
