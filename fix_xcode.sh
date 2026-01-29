#!/bin/bash
# Fix Xcode Path and Reset Simulators
# Run this with: bash fix_xcode.sh

echo "=========================================="
echo "🔧 Fixing iOS Simulator Setup"
echo "=========================================="
echo ""

echo "Step 1: Fixing Xcode Command Line Tools path..."
echo "This will ask for your password:"
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer

echo ""
echo "Step 2: Verifying path..."
XCODE_PATH=$(xcode-select -p)
echo "Xcode path: $XCODE_PATH"

if [[ "$XCODE_PATH" == "/Applications/Xcode.app/Contents/Developer" ]]; then
    echo "✅ Xcode path is correct!"
else
    echo "❌ Xcode path is still wrong. Please check if Xcode.app is in /Applications/"
    exit 1
fi

echo ""
echo "Step 3: Resetting simulators..."
xcrun simctl shutdown all 2>/dev/null
xcrun simctl erase all 2>/dev/null
echo "✅ Simulators reset!"

echo ""
echo "Step 4: Listing available simulators..."
xcrun simctl list devices | grep iPhone | head -5

echo ""
echo "=========================================="
echo "✅ Fix Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open Xcode"
echo "2. Open TreningsCoach/TreningsCoach.xcodeproj"
echo "3. Select a simulator (iPhone 16 Pro recommended)"
echo "4. Press ⌘R to build and run"
echo ""
