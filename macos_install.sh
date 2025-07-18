#!/bin/bash

echo "MM2 Macro - macOS Installation & Permission Setup"
echo "=================================================="

APP_PATH="/Users/$USER/Downloads/MM2-Macro-macOS.app"

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "❌ MM2-Macro-macOS.app not found in Downloads folder"
    echo "Please download and extract the zip file first"
    exit 1
fi

echo "✅ Found MM2-Macro-macOS.app"

# Remove quarantine attribute
echo "🔧 Removing quarantine flag..."
sudo xattr -rd com.apple.quarantine "$APP_PATH"

# Fix permissions
echo "🔧 Setting permissions..."
sudo chmod -R 755 "$APP_PATH"
sudo chmod +x "$APP_PATH/Contents/MacOS/MM2-Macro-macOS"

echo "✅ Basic setup complete!"
echo ""
echo "IMPORTANT: For keyboard shortcuts to work, you MUST:"
echo "1. Open System Preferences → Security & Privacy → Privacy"
echo "2. Click 'Input Monitoring' in the sidebar"
echo "3. Click the lock icon and enter your password"
echo "4. Check the box next to 'MM2-Macro-macOS'"
echo "5. Restart the application"
echo ""
echo "🚀 You can now run the app by double-clicking MM2-Macro-macOS.app"
echo ""
echo "If the app still won't start, try running from Terminal:"
echo "   $APP_PATH/Contents/MacOS/MM2-Macro-macOS"