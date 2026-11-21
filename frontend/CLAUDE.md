# Frontend

Verify before handing back with the `/verify` skill (tsc, jest, lint, web + android exports).

## Conventions and gotchas

- **R3F imports go through `@/features/cube/three/fiber`** (Metro picks `fiber.native.ts` on iOS/Android). ESLint blocks direct `@react-three/fiber` imports.
- **Canvas uses `frameloop="demand"`:** anything that changes the scene outside React props (gestures, animations) must call `invalidate()`, or it won't render.
- **Tests run on Jest (`jest-expo`), not Vitest.** TypeScript 6 doesn't auto-include `@types/*`; test globals come from `"types": ["jest", "node"]` in `tsconfig.json`.
- **Install Expo packages with `npx expo install`** so versions match the SDK.
