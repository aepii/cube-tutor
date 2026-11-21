# 0001 — Expo + react-native-web for one web and mobile codebase

**Status:** in effect · **Evidence:** the project goal in [`CLAUDE.md`](../../CLAUDE.md) ("runs on web and mobile from one codebase"); the boilerplate [`frontend/README.md`](../../frontend/README.md) shows it was created with `create-expo-app` (first commit `a13277a`); upgraded from SDK 54 to 58 in PR #3.

## Context
The app has to run in a browser (portfolio/demo) and on phones. It needs native 3D, gestures and secure token storage.

## Decision
One Expo app ([`frontend/`](../../frontend/)) with expo-router for file-based routing, react-native-web for the browser, and platform splits only where a library forces one:

- `three/fiber.ts` vs. `fiber.native.ts`, chosen by Metro's `.native.ts` resolution ([rendering.md](../rendering.md#web-vs-native-fiber)).
- Token storage: SecureStore on native, `localStorage` on web, via a `Platform.OS` check ([`features/auth/utils/storage.ts`](../../frontend/features/auth/utils/storage.ts)).
- Wheel zoom on web only (`Platform.OS` check in `SceneBridge`).

## Alternatives
- Separate web (React + DOM three.js) and native apps. *Inferred:* doubles the UI and gesture work.
- Bare React Native without Expo. *Inferred:* gives up Expo Go for on-device testing and `npx expo install` version alignment, both of which the workflow relies on ([`CLAUDE.md`](../../CLAUDE.md)).
- Flutter or another non-JS stack. Not considered anywhere in the repo.

## Consequences
- \+ One codebase and one gesture system (gesture-handler 3 works on web and native).
- \+ Expo Go makes phone testing a QR scan away.
- − Every 3D or input feature has to work on two renderers (DOM canvas and `expo-gl`). The R3F import wrapper and its ESLint rule exist only because of this.
- − SDK upgrades pin many package versions together, so packages must be installed with `npx expo install`.
- − Web-only concerns (CORS for `localhost:8081`, `touchAction: "none"`, wheel events) leak into shared code.
