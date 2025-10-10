#!/bin/bash

API_KEY="013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197"
API_URL="http://35.226.93.88:8080"

echo "🧪 Test 1: Create Build with City Theme"
echo "========================================"
echo ""

# Create build
BUILD_RESPONSE=$(curl -s -X POST "$API_URL/build" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "game_id": "theme-integration-test",
    "game_name": "City Theme Test",
    "game_type": "runner",
    "theme": "city",
    "assets": []
  }')

echo "Build Response:"
echo "$BUILD_RESPONSE" | python3 -m json.tool

BUILD_ID=$(echo "$BUILD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['build_id'])" 2>/dev/null)

if [ -z "$BUILD_ID" ]; then
  echo "❌ Failed to create build"
  exit 1
fi

echo ""
echo "✅ Build created: $BUILD_ID"
echo ""
echo "Monitoring build status..."
echo "========================================"

# Monitor build progress
for i in {1..60}; do
  STATUS_RESPONSE=$(curl -s "$API_URL/build/$BUILD_ID/status" \
    -H "Authorization: Bearer $API_KEY")
  
  STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
  PROGRESS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['progress'])" 2>/dev/null)
  MESSAGE=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['message'])" 2>/dev/null)
  
  echo "[$i] Status: $STATUS | Progress: $PROGRESS% | $MESSAGE"
  
  if [ "$STATUS" == "completed" ]; then
    echo ""
    echo "✅ Build Completed!"
    echo ""
    echo "Full Response:"
    echo "$STATUS_RESPONSE" | python3 -m json.tool
    
    PLAY_URL=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('play_url', 'N/A'))" 2>/dev/null)
    echo ""
    echo "🎮 Play URL: $PLAY_URL"
    echo ""
    echo "BUILD_ID=$BUILD_ID" > /tmp/theme_test_build_id.txt
    exit 0
  fi
  
  if [ "$STATUS" == "failed" ]; then
    echo ""
    echo "❌ Build Failed!"
    echo "$STATUS_RESPONSE" | python3 -m json.tool
    exit 1
  fi
  
  sleep 15
done

echo ""
echo "⏰ Build timeout after 15 minutes"
exit 1
