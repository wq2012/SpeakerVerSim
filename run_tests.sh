#!/bin/bash
set -o errexit

flake8 .
pytype .
