import { LIGHTING_CONSTANTS } from "@/constants";

export default function CubeLighting() {
  return <ambientLight intensity={LIGHTING_CONSTANTS.AMBIENT_INTENSITY} />;
}
