#!/bin/bash
export PYTHONDONTWRITEBYTECODE=1
ROOT=`dirname "${BASH_SOURCE[0]}"`
act="${ROOT}/.venv/bin/activate"

if [ ! -f "${act}" ]; then
    set -e
    python3 -m venv .venv
    source ${act}
    pip install pip wheel --upgrade
    pip install -r requirements.txt
    set +e
else
    source ${act}
fi

source ./local.env

source .venv/bin/activate
./process_domain_aliases.py $@
deactivate
