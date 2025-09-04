#!/bin/bash
set FLASK_APP = "./Short_URL/main.py"

echo "Running Flask App bootstrap"

# setup the test db
pipenv run flask initdb

# Run Flask with pipenv
pipenv run flask --debug run -h 0.0.0.0