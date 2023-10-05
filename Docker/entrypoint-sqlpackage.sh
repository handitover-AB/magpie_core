#!/usr/bin/env bash

# Install sqlpackage:
export PATH="$PATH:/root/.dotnet/tools"
echo -n "Installing sqlpackage..."
dotnet tool install Microsoft.SqlPackage -g > /dev/null
echo "OK"

# Pass all arguments to the sqlpackage command:
sqlpackage "$@" | grep --line-buffered "Processing Import"
