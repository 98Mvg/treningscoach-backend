# Fix iOS Simulator Launch Error

## Problem
```
Simulator device failed to launch com.mariusgaarder.TreningsCoach.
Domain: NSPOSIXErrorDomain
Code: 3
Failure Reason: No such process
```

## Quick Fixes (Try in Order)

### Fix 1: Reset Simulator (Most Common) ⭐

**In Xcode:**
1. **Menu Bar** → **Window** → **Devices and Simulators**
2. Select the simulator that failed
3. **Right-click** → **Delete**
4. Click **+** button to create a new iPhone simulator
5. Try running again (⌘R)

**Or use Terminal:**
```bash
# Kill all simulators
killall Simulator

# Erase the simulator
xcrun simctl erase all

# Restart Xcode
killall Xcode
```

### Fix 2: Reset Xcode Command Line Tools Path

```bash
# Set correct Xcode path
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer

# Verify
xcode-select -p
# Should show: /Applications/Xcode.app/Contents/Developer

# Accept license
sudo xcodebuild -license accept
```

### Fix 3: Clean Build Folder

**In Xcode:**
1. **Product** → **Clean Build Folder** (⇧⌘K)
2. Close Xcode
3. Delete derived data:
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData/*
   ```
4. Restart Xcode
5. Build and run (⌘R)

### Fix 4: Reset All Simulators

```bash
# Shutdown all simulators
xcrun simctl shutdown all

# Erase all simulators
xcrun simctl erase all

# List available devices
xcrun simctl list devices

# Boot a specific simulator
xcrun simctl boot "iPhone 16 Pro"

# Open Simulator app
open -a Simulator
```

### Fix 5: Restart macOS

Sometimes simulator gets stuck and needs a full restart:
```bash
sudo reboot
```

---

## Step-by-Step Fix (Recommended)

### 1. Fix Xcode Command Line Tools
```bash
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
```

### 2. Kill Everything
```bash
killall Simulator
killall Xcode
```

### 3. Clean Derived Data
```bash
rm -rf ~/Library/Developer/Xcode/DerivedData/*
```

### 4. Reset Simulators
```bash
xcrun simctl shutdown all
xcrun simctl erase all
```

### 5. Open Xcode Fresh
1. Open Xcode
2. Open project: `TreningsCoach/TreningsCoach.xcodeproj`
3. Select a simulator from the top bar (e.g., iPhone 16 Pro)
4. Press ⌘R to build and run

---

## Alternative: Use Real Device

If simulator keeps failing, test on a real iPhone:

### Setup
1. **Plug in iPhone** via USB
2. **Trust computer** on iPhone (popup)
3. **Xcode** → Select your iPhone from device dropdown
4. **Update Config.swift** to use your Mac's IP:
   ```swift
   static let localURL = "http://192.168.10.87:10000"
   static let backendURL = localURL
   ```
5. Press ⌘R to build and run on device

### Enable Developer Mode (iOS 16+)
If Xcode says "Developer Mode disabled":
1. iPhone → **Settings** → **Privacy & Security**
2. Scroll down → **Developer Mode**
3. Toggle **ON**
4. Restart iPhone

---

## Check Simulator Status

### List All Simulators
```bash
xcrun simctl list devices
```

### Check Booted Simulators
```bash
xcrun simctl list devices | grep Booted
```

### Boot Specific Simulator
```bash
xcrun simctl boot "iPhone 16 Pro"
```

---

## If Still Failing

### Check System Logs
```bash
# View simulator logs
tail -f ~/Library/Logs/CoreSimulator/CoreSimulator.log
```

### Reinstall Xcode Simulators
1. **Xcode** → **Settings** (⌘,)
2. **Platforms** tab
3. Find **iOS**
4. Click **Download** to reinstall simulators

### Nuclear Option (Last Resort)
```bash
# Delete ALL Xcode data
rm -rf ~/Library/Developer/Xcode
rm -rf ~/Library/Developer/CoreSimulator
rm -rf ~/Library/Caches/com.apple.dt.Xcode

# Restart Xcode and reinstall simulators
```

---

## Expected Working State

After fixes, you should see:
```bash
$ xcode-select -p
/Applications/Xcode.app/Contents/Developer

$ xcrun simctl list devices | grep Booted
    iPhone 16 Pro (79C9F3C6...) (Booted)
```

Then build and run works! ✅

---

## Quick Test Script

Save this as `test_simulator.sh`:

```bash
#!/bin/bash
echo "🧪 Testing iOS Simulator Setup"
echo ""

echo "1. Checking Xcode path..."
xcode-select -p

echo ""
echo "2. Checking simulators..."
xcrun simctl list devices | grep iPhone | head -5

echo ""
echo "3. Checking booted simulators..."
BOOTED=$(xcrun simctl list devices | grep Booted)
if [ -z "$BOOTED" ]; then
    echo "   ⚠️  No simulators booted"
else
    echo "   ✅ $BOOTED"
fi

echo ""
echo "4. Backend server status..."
curl -s http://localhost:10000/health | grep status || echo "   ⚠️  Backend not running"

echo ""
echo "Done! If all checks pass, try building again."
```

Run it:
```bash
chmod +x test_simulator.sh
./test_simulator.sh
```

---

## TL;DR - Quick Fix

```bash
# 1. Fix Xcode path
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer

# 2. Reset everything
killall Simulator Xcode
rm -rf ~/Library/Developer/Xcode/DerivedData/*
xcrun simctl shutdown all
xcrun simctl erase all

# 3. Restart Xcode and try again
```

This fixes 90% of simulator launch issues! 🚀
