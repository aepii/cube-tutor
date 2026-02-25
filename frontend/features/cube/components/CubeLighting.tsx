import { LIGHTING_CONSTANTS } from "@/features/cube/constants/lighting.constants";

export default function CubeLighting() {
  return <ambientLight intensity={LIGHTING_CONSTANTS.AMBIENT_INTENSITY} />;
}
