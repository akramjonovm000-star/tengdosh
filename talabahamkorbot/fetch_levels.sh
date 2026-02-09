#!/bin/bash
# Source env to get token
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Fallback token if not in env
if [ -z "$HEMIS_ADMIN_TOKEN" ]; then
    echo "Token not found in .env"
    exit 1
fi

echo "Fetching Levels..."
curl -k -s -H "Authorization: Bearer $HEMIS_ADMIN_TOKEN" "https://student.jmcu.uz/rest/v1/education/level-list"
echo ""
echo "Done."
