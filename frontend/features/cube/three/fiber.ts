// Web entry for react-three-fiber.
// Metro resolves `fiber.native.ts` instead on iOS/Android, so all cube code
// imports R3F from "@/features/cube/three/fiber" and gets the right build.
export { Canvas, invalidate, useFrame, useThree } from "@react-three/fiber";
