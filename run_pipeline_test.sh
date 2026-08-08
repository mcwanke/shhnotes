#!/bin/bash
export LD_LIBRARY_PATH="/home/bigfoot/code_projects/project-shhnotes/shhnotes/venv/lib/python3.14/site-packages/nvidia/cu13/lib:$LD_LIBRARY_PATH"
source venv/bin/activate
python3 test_pipeline.py
