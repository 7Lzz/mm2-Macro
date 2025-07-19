# Seven's MM2 Macro

## ⚠️ EARLY BETA WARNING ⚠️

This application is currently in **early beta** and is **NOT ready for general ease-of-use**. Expect bugs, crashes, and the need for technical troubleshooting. This tool is intended for advanced users who are comfortable with Python environments and debugging issues.

## Overview

Seven's MM2 Macro is an automation tool designed for Murder Mystery 2 (MM2) on Roblox. It provides a collection of pre-programmed macros to execute various in-game actions and movement techniques through customizable keybinds.

## Key Features

- **Multiple Macro Types**: Quick setup routines, movement clips (bouncy twirl, flex walk, etc.), bomb jumps, speed glitches, and more
- **Customizable Keybinds**: Assign keyboard keys or mouse buttons to any macro
- **Smart Focus Detection**: Automatically detects when Roblox is active and only functions when the game is focused
- **Item Slot Configuration**: Configurable item slots for GG Signs, Prank Bombs, and other tools
- **Real-time Status Monitoring**: Live status updates showing macro availability and game focus
- **Settings Persistence**: Automatically saves window position, keybinds, and configuration
- **Safety Features**: Toggle macros on/off, always-on-top window option, etc.

## Requirements

**This application requires multiple Python dependencies that are NOT automatically installed:**

```bash
pip install keyboard mouse pywin32 PyQt5 pynput psutil
