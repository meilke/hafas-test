#!/bin/bash

access_id=${1}
search_string=${2}
max_no=${3:-1}
base_url=${4:-http://demo.hafas.de/openapi/vbb-proxy}

curl \
    -G -s \
    "${base_url}/location.name?accessId=${access_id}&format=json&maxNo=${max_no}" \
    --data-urlencode "input=${search_string}" \
    | jq \
        '.stopLocationOrCoordLocation[].StopLocation | {name: .name, extId: .extId, id: .id}' \
        -r
