# My Cricket 360 — iOS (SwiftUI)

One native app for all clubs. Global user account, membership requests per club, club switcher for approved memberships, last club + access token in Keychain.

## Requirements

- macOS with Xcode 15+
- [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`)
- API running at `http://127.0.0.1:8400` (or set `MC360APIBaseURL` in Info.plist)
- Optional: Supabase publishable URL + anon key for project **mycricket360** (org `personalyogesh`)

```bash
cp Config/Debug.xcconfig.example Config/Debug.xcconfig
# Fill SUPABASE_URL and SUPABASE_ANON_KEY only — never service_role or DB password
```

## Generate & run

```bash
cd apps/ios
xcodegen generate
open MyCricket360.xcodeproj
xcodebuild \
  -project MyCricket360.xcodeproj \
  -scheme MyCricket360 \
  -destination 'generic/platform=iOS Simulator' \
  -configuration Debug \
  CODE_SIGNING_ALLOWED=NO \
  build
```

Select an iOS Simulator, then Run. `generic/platform=iOS Simulator` compiles without a named device. A named destination such as `platform=iOS Simulator,name=iPhone 16` also works when that simulator is installed.

> **Note:** This repository’s Linux agents do **not** compile the iOS target. Do not treat the shell as “build verified” until Xcode succeeds on macOS.

## Demo flow (dev auth)

1. Tap **Continue with demo account** → `POST /v1/auth/dev-token`.
2. Request Starks and/or Steelers membership from **Clubs**.
3. Promote/approve via API admin tools; approved clubs appear in the switcher.
4. **Sponsors** lists **published** sponsors only for the selected club.

## Networking

Typed DTOs in `Networking/APIModels.swift` aligned with `packages/openapi/openapi.json`.
