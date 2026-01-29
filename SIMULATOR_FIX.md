# iOS Simulator Launch Fix

## Error
```
Simulator device failed to launch com.mariusgaarder.TreningsCoach.
Domain: NSPOSIXErrorDomain
Code: 3
Failure Reason: No such process
```

## Quick Fixes (Try in Order)

### 1. Reset Simulator (Fast Fix)
In Xcode:
1. **Device** menu → **Erase All Content and Settings...**
2. Confirm erase
3. Wait for simulator to restart
4. Run app again

### 2. Clean Build (Medium Fix)
In Xcode:
1. **Product** → **Clean Build Folder** (Cmd+Shift+K)
2. **Product** → **Build** (Cmd+B)
3. Run app again (Cmd+R)

### 3. Restart Simulator (Medium Fix)
1. Quit Simulator app completely (Cmd+Q)
2. In Xcode: **Product** → **Destination** → Select your iPhone simulator
3. Run app again (Cmd+R)

### 4. Delete Derived Data (Strong Fix)
In Xcode:
1. **Window** → **Organizer** (or Cmd+Shift+2)
2. Click **Projects** tab
3. Find **TreningsCoach** project
4. Click **Delete** next to "Derived Data"
5. Close Organizer
6. **Product** → **Clean Build Folder** (Cmd+Shift+K)
7. Run app again (Cmd+R)

### 5. Restart Everything (Nuclear Option)
```bash
# 1. Quit Xcode completely (Cmd+Q)

# 2. Kill all simulator processes
killall -9 "Simulator"
killall -9 "SimulatorTrampoline"

# 3. Open Xcode again
open -a Xcode

# 4. Wait 30 seconds for Xcode to fully load
# 5. Run app (Cmd+R)
```

### 6. Check Backend is Running
Make sure backend is accessible from simulator:

```bash
# Check backend is running
curl http://127.0.0.1:10000/health

# Should return:
# {"status":"healthy","version":"1.1.0"}

# If not running, start it:
cd backend
./start_backend.sh
```

## Most Common Causes

1. **Simulator cache corruption** → Fix #1 (Reset Simulator)
2. **Build artifacts conflict** → Fix #2 (Clean Build)
3. **Derived data corruption** → Fix #4 (Delete Derived Data)
4. **Backend not running** → Fix #6 (Start Backend)

## Recommended Fix Order

**Try this sequence:**
1. Reset Simulator (1 minute)
2. Clean Build (1 minute)
3. If still failing → Delete Derived Data (2 minutes)
4. If still failing → Restart Everything (3 minutes)

## Alternative: Use Physical Device

If simulator keeps failing, run on a real iPhone:
1. Connect iPhone via USB
2. Trust computer on iPhone
3. In Xcode: **Product** → **Destination** → Select your iPhone
4. Run app (Cmd+R)

**Note**: Backend URL needs to be updated for physical device:
- Change `localhost:10000` to your Mac's IP: `192.168.10.87:10000`
- Update in `Config.swift`

## Verify Backend Connection

Once app launches, check backend logs:
```bash
# Watch for connection attempts
tail -f /tmp/backend.log

# You should see requests like:
# 127.0.0.1 - - [29/Jan/2026 21:00:00] "GET /health HTTP/1.1" 200 -
```

## Still Not Working?

Check Xcode console for specific error messages:
1. Run app (Cmd+R)
2. Look at bottom console in Xcode
3. Search for error messages about network, permissions, or missing files

Common issues:
- **"Failed to connect"** → Backend not running
- **"Permission denied"** → Microphone permissions (should auto-prompt)
- **"App failed to install"** → Clean build + Delete derived data

---

**Quick Command Summary:**
```bash
# Reset everything (from scratch)
killall -9 "Simulator"
cd /Users/mariusgaarder/Documents/treningscoach/backend
./start_backend.sh

# Then in Xcode:
# Product → Clean Build Folder (Cmd+Shift+K)
# Device → Erase All Content and Settings
# Product → Run (Cmd+R)
```

This should get you running!
