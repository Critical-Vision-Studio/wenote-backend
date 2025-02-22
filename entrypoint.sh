#!/bin/env sh

if [ "$DEBUG" = "1" ]; then
  echo "Running in debug mode"
  exec python -m pdb main.py
else
  echo "Running with Gunicorn"
  exec gunicorn main:app -b 0.0.0.0:8080
fi

