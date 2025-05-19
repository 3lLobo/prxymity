#!/bin/bash

#  start minikube
#minikube start

# Load .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi
echo $(env | grep ES)
# Load python venv
if [ -d .venv ]; then
    source .venv/bin/activate
else
    echo "Python virtual environment not found. Please create it first."
    exit 1
fi

# start the proxy in background
mitmdump -s run_addons.py -m reverse:$LLM_HOST@$RP_PORT &

# run license script
python es_license.py --es_url $ES_HOST --username $ES_USER --password $ES_PASSWORD --insecure --license_file $LICENSE_FILE
