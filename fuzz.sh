#!/bin/bash

python3 csmith.py
echo "SHOULD_UPLOAD_ARTIFACT=$?" >> $GITHUB_OUTPUT
