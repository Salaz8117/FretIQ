# FretIQ Mobile App Setup 📱

This guide explains how to build native Android (APK/AAB) and iOS apps from the FretIQ PWA using Capacitor.

## Prerequisites

### For Android
- **Android Studio** (latest) with Android SDK
- **JDK 17+**
- **Node.js 18+**
- **Git**

### For iOS (macOS only)
- **Xcode 15+** with iOS SDK
- **CocoaPods** (`sudo gem install cocoapods`)
- **Node.js 18+**

## Quick Start

```bash
cd frontend

# 1. Install dependencies (includes Capacitor)
npm install

# 2. Build the web app
npm run build

# 3. Initialize Capacitor (first time only)
npm run cap:init

# 4. Add platforms
npm run cap:add:android
npm run cap:add:ios

# 5. Sync web assets to native projects
npm run cap:sync
```

## Android Build

### Development Build
```bash
# Open Android Studio
npm run cap:open:android
```

### Production APK/AAB
```bash
# Generate release keystore (one-time)
keytool -genkey -v -keystore release-key.keystore -alias fretiq -keyalg RSA -keysize 2048 -validity 10000

# Configure keystore in capacitor.config.json
# Then build
npm run build
npm run cap:sync
npm run cap:build:android

# Or manually in Android Studio:
# Build > Generate Signed Bundle/APK
```

### Output Locations
- **APK**: `android/app/build/outputs/apk/release/app-release.apk`
- **AAB** (Play Store): `android/app/build/outputs/bundle/release/app-release.aab`

## iOS Build (macOS only)

```bash
# Open Xcode
npm run cap:open:ios

# In Xcode:
# 1. Select your Team (Apple Developer account)
# 2. Update Bundle Identifier if needed
# 3. Product > Archive > Distribute App
```

## PWA Alternative (No Native Build Required)

The app works as a **Progressive Web App** on any device:

1. Open `https://your-domain.com` in Chrome/Edge/Safari
2. Tap "Install" in address bar or browser menu
3. App installs like native with:
   - Offline support
   - Home screen icon
   - Fullscreen mode
   - Push notifications (when configured)

### PWA Features Enabled
- Auto-update service worker
- Offline caching for API/UG requests
- Custom icons (192x192, 512x512)
- App shortcuts (Search Chords)
- Portrait orientation lock
- Theme colors

## Configuration

### Capacitor Config
Edit `capacitor.config.json`:
- `appId`: Unique identifier (e.g., `com.fretiq.app`)
- `appName`: Display name
- `server.url`: Production domain for live reload
- Android/iOS specific settings

### Icons & Splash Screens
```bash
# Generate from source image (1024x1024)
npx @capacitor/assets generate --iconBackgroundColor "#6366f1" --splashBackgroundColor "#6366f1"
```

### Permissions
Add to `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

Add to `ios/App/App/Info.plist`:
```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

## CI/CD with GitHub Actions

### Android
```yaml
# .github/workflows/android.yml
name: Android Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - uses: actions/setup-java@v4
        with: { distribution: 'temurin', java-version: '17' }
      - run: cd frontend && npm ci && npm run build
      - uses: android-actions/setup-android@v3
      - run: cd frontend && npm run cap:sync android
      - run: cd frontend/android && ./gradlew assembleRelease
      - uses: actions/upload-artifact@v4
        with:
          name: apk
          path: frontend/android/app/build/outputs/apk/release/*.apk
```

### iOS (requires macOS runner)
```yaml
# .github/workflows/ios.yml
name: iOS Build
on: [push]
jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: cd frontend && npm ci && npm run build
      - run: cd frontend && npm run cap:sync ios
      - run: cd frontend/ios && xcodebuild -workspace App.xcworkspace -scheme App -configuration Release -archivePath build/App.xcarchive archive
      - run: cd frontend/ios && xcodebuild -exportArchive -archivePath build/App.xcarchive -exportPath build -exportOptionsPlist ExportOptions.plist
```

## Testing on Device

### Android
```bash
# USB Debugging enabled on device
adb devices
npm run cap:open:android
# Run in Android Studio
```

### iOS
```bash
# Connect iPhone via USB
# Trust computer on device
npm run cap:open:ios
# Run in Xcode
```

## Troubleshooting

### "Capacitor not found"
```bash
npm install @capacitor/cli @capacitor/core @capacitor/android @capacitor/ios
```

### "Gradle build failed"
```bash
cd frontend/android
./gradlew clean
cd ..
npm run cap:sync android
```

### "CocoaPods error"
```bash
cd frontend/ios/App
pod deintegrate
pod install
cd ../..
```

### "Web assets not loading"
```bash
npm run build
npm run cap:sync
```

## App Store Submission

### Google Play Store
1. Build AAB: `npm run cap:build:android`
2. Upload to Play Console
3. Complete store listing
4. Submit for review

### Apple App Store
1. Archive in Xcode
3. Upload to App Store Connect
4. Complete store listing
5. Submit for review

## Resources

- [Capacitor Docs](https://capacitorjs.com/docs)
- [Android App Signing](https://developer.android.com/studio/publish/app-signing)
- [App Store Connect](https://appstoreconnect.apple.com/)
- [PWA Checklist](https://web.dev/pwa-checklist/)