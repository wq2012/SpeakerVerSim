"""Setup script for the package."""

import setuptools

VERSION = "0.1.3"
DESCRIPTION = (
    "Simulation framework for version control strategies "
    "of speaker recognition systems.")

with open("README.md", "r") as file_object:
    LONG_DESCRIPTION = file_object.read()

with open("requirements.txt") as file_object:
    INSTALL_REQUIRES = file_object.read().splitlines()

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
    install_requires=INSTALL_REQUIRES,
)
