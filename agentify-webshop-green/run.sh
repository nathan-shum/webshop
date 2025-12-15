#!/bin/bash
if [ -f "/opt/miniconda3/envs/webshop-py313/bin/python" ]; then
    PYTHON_EXEC="/opt/miniconda3/envs/webshop-py313/bin/python"
else
    PYTHON_EXEC="python"
fi
$PYTHON_EXEC main.py run
