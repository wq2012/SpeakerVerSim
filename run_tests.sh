#!/bin/bash
set -o errexit

# clean up
rm -rf build
rm -rf dist
rm -rf SpeakerVerSim.egg-info

pytype .
flake8 .
pytest .
