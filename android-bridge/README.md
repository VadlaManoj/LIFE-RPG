# LIFE RPG — Android Health Connect Companion Bridge

This minimal Android companion bridge connects **Android Health Connect** directly to the **LIFE RPG** backend without requiring a second full mobile application or deprecated Google Fit REST APIs.

## Architecture

```
[Android Health Connect API]
           ↓
[HealthConnectManager.kt] (Reads Steps & Exercise Sessions)
           ↓
[BridgeSyncClient.kt] (Authenticates with LIFE RPG Pairing Token)
           ↓ HTTPS / JSON
[POST /api/integrations/fitness/health-connect/sync]
           ↓
[LIFE RPG Unified Activity Layer]
           ↓
[Quest Matching & Validation]
           ↓
[XP + Coins + Skill Updates]
```

## Permissions Requested
- `android.permission.health.READ_STEPS`
- `android.permission.health.READ_EXERCISE`
- `android.permission.health.READ_DISTANCE`
- `android.permission.health.READ_TOTAL_CALORIES_BURNED`

## Setup & Testing Instructions

1. **Prerequisites**:
   - Android SDK 35 / Android Studio or Gradle 8.5+.
   - Android device or emulator running Android 14+ (or Android 9-13 with Google Health Connect installed from Play Store).
   - In emulator, install the **Health Connect Toolbox** to generate test workout sessions and steps.

2. **Obtain Pairing Token**:
   - In LIFE RPG Web UI, navigate to **Integrations → Fitness (Health Connect)**.
   - Click **Show Bridge Pairing Code & Token**.
   - Copy your secure pairing token.

3. **Sync Activity**:
   - Open the companion bridge app on your Android device.
   - Enter your backend URL (`http://10.0.2.2:8000` for Android emulator or LAN IP `http://192.168.x.x:8000`).
   - Paste your pairing token.
   - Click **1. Request Health Connect Permissions** and allow access.
   - Click **2. Sync Health Activity to LIFE RPG**.

Activity sessions and step counts will be immediately normalized and matched against your active fitness, walking, running, and habit quests!
