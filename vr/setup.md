# Unity VR Setup Guide for Meta Quest 3

## Prerequisites

### Unity Installation
1. Download and install [Unity Hub](https://unity.com/download)
2. During Unity installation, ensure you select:
   - Android Build Support
   - Android Studio NDK
   - Android SDK & Tools
   - Visual Studio Code
   > Note: Missing VSCode may cause build failures

### Required Meta Packages
1. [Meta XR Core SDK](https://assetstore.unity.com/packages/tools/integration/meta-xr-core-sdk-269169)
2. [Meta XR Simulator](https://assetstore.unity.com/packages/tools/integration/meta-xr-simulator-266732)

## Configuration Steps

### XR Plugin Setup
1. Navigate to Project Settings > XR Plug-in Management
2. Select the OpenXR tab (not Plugin)
3. Under Interaction Profiles, enable:
   - Hand Tracking Subsystem
   - Meta Hand Tracking Aim
   - Meta Quest Support (Android only)

### Building for Quest
1. Switch build target to Android
   - File > Build Settings > Android
2. Build the example scene to verify setup

### Hand Tracking Setup

#### For MacOS Users
1. Go to Edit > Project Settings
2. Enable the following options:
   ![Hand Tracking Settings](https://github.com/user-attachments/assets/16793b4e-6c27-4d0e-a4ca-1bafbae6bd5a)

3. Create a new script at `Assets/Scripts/HandCover.cs` for hand tracking functionality

## Troubleshooting
- If build fails, verify all Android dependencies are properly installed
- Ensure Meta XR packages are compatible with your Unity version
- Check that hand tracking is enabled in Quest device settings

## Notes
- If you get an error about `libmetal.dylib` not being found, you may need to add it to your path.
