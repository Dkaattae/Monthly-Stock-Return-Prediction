#!/bin/bash

BODY=$(jq -c '.[0]' json_records.json)

curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -H "Content-Type: application/json" \
  -d '{"httpMethod": "POST", "path": "/predict", "body":"{\"date\":1751328000000,\"ticker\":\"A\",\"alpha\":-0.0006559764,\"beta\":0.9498632784,\"month_index\":24,\"index_avg\":0.0024422721,\"historical_vol\":0.0137960029,\"eom_10yr\":4.24,\"10yr_avg\":4.3833333333,\"spread\":0.52,\"vix_avg\":18.2150001526,\"sector\":\"Healthcare\"}", "isBase64Encoded": false}'

curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations \
  -H "Content-Type: application/json" \
  -d '{"httpMethod": "POST", "path": "/predict", "body":'"$BODY"', "isBase64Encoded": false}'

curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"httpMethod":"POST","path":"/predict","headers":{"Content-Type":"application/json"},"body":"{\"your\":\"payload\"}","isBase64Encoded":false}'


jq -n --argjson body "$BODY" \
  '{
    httpMethod: "POST",
    path: "/predict",
    headers: {"Content-Type": "application/json"},
    body: $body,
    isBase64Encoded: false
  }' | \
curl -X POST -H "Content-Type: application/json" -d @- http://localhost:9000/2015-03-31/functions/function/invocations