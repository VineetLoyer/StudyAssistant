TOKEN="$1"
curl -s -X POST "$2/mcp/tools/load_material" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-user-id: vineet@test" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "Spark-Scala",
    "type": "pptx",
    "range": "slides 1-5",
    "local_path": "./samples/2-Spark-Scala.pptx"
  }'