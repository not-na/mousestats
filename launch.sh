#!/usr/bin/env bash

# From https://stackoverflow.com/a/16349776
cd "${0%/*}"

source mousestats-py/bin/activate

python3 main.py