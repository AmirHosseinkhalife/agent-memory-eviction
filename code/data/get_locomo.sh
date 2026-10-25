#!/usr/bin/env sh
# Download the LoCoMo benchmark (Maharana et al., ACL 2024; CC BY-NC 4.0).
set -e
cd "$(dirname "$0")/locomo"
curl -sSL -o locomo10.json https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json
echo "saved $(pwd)/locomo10.json"
