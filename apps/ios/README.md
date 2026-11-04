# My Cricket 360 — iOS (SwiftUI)

One native app for all clubs. Global user account, membership requests per club, club switcher for approved memberships, last club persisted in Keychain.

## Requirements

- macOS with Xcode 15+
- [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`) recommended

## Generate & run

```bash
cd apps/ios
xcodegen generate
open MyCricket360.xcodeproj
```

Select an iOS Simulator, then Run.

### Demo flow

1. Tap **Continue with demo account**.
2. Starks is approved; Steelers is pending — switcher only lists approved clubs.
3. Request Steelers/Starks from the **Clubs** tab (idempotent while pending/approved).
4. Last selected club is stored in the Keychain (`org.mycricket360.app`).

## Notes

- UI gating is advisory; production data access must be authorized by the FastAPI backend.
- This Linux CI environment cannot compile SwiftUI; verify builds on macOS.
- Do not point production DNS or Firebase at this app without approval.
