#!/bin/bash

access_id=${1}
origin=${2}
dest=${3}
rt_mode=${4:-SERVER_DEFAULT}
base_url=${5:-http://demo.hafas.de/openapi/vbb-proxy}

curl \
    -G -s \
    "${base_url}/trip?accessId=${access_id}&format=json" \
    --data-urlencode "originExtId=${origin}" \
    --data-urlencode "destExtId=${dest}" \
    --data-urlencode "rtMode=${rt_mode}" \
    | jq \
        '.Trip[]|{name: .LegList.Leg[0].Product.line, start: .LegList.Leg[0].Origin.time, startRT: .LegList.Leg[0].Origin.rtTime, end: .LegList.Leg[-1].Destination.time, endRT: .LegList.Leg[-1].Destination.rtTime, ctxRecon: .ctxRecon}' \
        -r
