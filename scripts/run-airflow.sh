#!/bin/bash

export AIRFLOW_HOME="$PWD/.airflow"
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES="False"
export AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION="False"

uv run mp \
  'uv run airflow api-server' \
  'uv run airflow standalone'