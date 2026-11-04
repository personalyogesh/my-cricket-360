# My Cricket 360 — iOS (SwiftUI)

One native app for all clubs. Global user account, membership requests per club, club switcher for approved memberships, last club + access token in Keychain.

## Requirements

- macOS with Xcode 15+
- [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`)
- API running at `http://127.0.0.1:8400` (or set `MC360APIBaseURL` in Info.plist)

## Generate & run

```bash
cd apps/ios
xcodegen generate
open MyCricket360.xcodeproj
```

Select an iOS Simulator, then Run.

> **Note:** This repository’s Linux agents do **not** compile the iOS target. Do not treat the shell as “build verified” until Xcode succeeds on macOS.

## Demo flow (dev auth)

1. Tap **Continue with demo account** → `POST /v1/auth/dev-token`.
2. Request Starks and/or Steelers membership from **Clubs**.
3. Promote/approve via API admin tools; approved clubs appear in the switcher.
4. **Sponsors** lists **published** sponsors only for the selected club.

## Networking

Typed DTOs in `Networking/APIModels.swift` aligned with `packages/openapi/openapi.json`.
