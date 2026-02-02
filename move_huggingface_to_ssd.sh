#!/bin/bash

echo "📦 Moving Hugging Face cache to SSD"
echo "===================================="
echo ""

SSD_PATH="/Volumes/SSD"
HF_CACHE=~/.cache/huggingface
NEW_LOCATION="$SSD_PATH/huggingface_cache"

# Check if SSD is mounted
if [ ! -d "$SSD_PATH" ]; then
    echo "❌ SSD not found at $SSD_PATH"
    echo "   Please connect your external SSD and try again"
    exit 1
fi

echo "✅ SSD found: $SSD_PATH"
echo ""
echo "Current cache: $HF_CACHE (4.2GB)"
echo "New location:  $NEW_LOCATION"
echo ""
echo "This will:"
echo "  1. Copy cache to SSD (takes ~2 minutes)"
echo "  2. Create backup of original"
echo "  3. Create symlink to SSD"
echo "  4. Your treningscoach app will work unchanged"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Create directory on SSD
echo ""
echo "📁 Creating directory on SSD..."
mkdir -p "$NEW_LOCATION"

# Copy (not move yet, to be safe)
echo ""
echo "📋 Copying cache to SSD (this takes ~2 minutes)..."
rsync -av --progress "$HF_CACHE/" "$NEW_LOCATION/"

if [ $? -ne 0 ]; then
    echo "❌ Copy failed"
    exit 1
fi

echo ""
echo "✅ Copy complete!"
echo ""

# Backup original
echo "💾 Creating backup of original..."
mv "$HF_CACHE" "${HF_CACHE}.backup"

# Create symlink
echo "🔗 Creating symlink..."
ln -s "$NEW_LOCATION" "$HF_CACHE"

echo ""
echo "✅ Done! Hugging Face cache moved to SSD"
echo ""
echo "Verification:"
ls -lh "$HF_CACHE"
echo ""
echo "Your treningscoach app will continue to work normally."
echo "The voice cloning will load from: $NEW_LOCATION"
echo ""
echo "To test, try running the backend:"
echo "  cd backend && PORT=10000 python3 main.py"
echo ""
echo "If everything works, remove the backup to free up space:"
echo "  rm -rf ${HF_CACHE}.backup"

