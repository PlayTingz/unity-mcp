#!/bin/bash
set -e

echo "Activating Unity Pro license..."
/opt/unity/editors/2022.3.45f1/Editor/Unity \
  -batchmode \
  -quit \
  -nographics \
  -logFile /tmp/unity-activate-pro.log \
  -username 'dev@playtingz.com' \
  -password 'UnityDev2025!'

echo "Activation complete. Checking license status..."
sleep 5

# Check if license was activated
if grep -q "Pro License: YES" /tmp/unity-activate-pro.log; then
  echo "✅ Unity Pro license activated successfully!"
  exit 0
else
  echo "❌ License activation failed. Log:"
  cat /tmp/unity-activate-pro.log | tail -50
  exit 1
fi
