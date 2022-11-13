#!/bin/bash

set - euo pipefail

declare OWN_FILENAME="$(basename $0 .sh)"
declare LAMBDA_EXTENSION_NAME="$OWN_FILENAME"
 
echo "${LAMBDA_EXTENSION_NAME}  launching extension"
python3 "/opt/extensions/${LAMBDA_EXTENSION_NAME}/extension.py"
