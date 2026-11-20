import { CubeProps } from "@/features/cube/types/cube.types";
import { useCubeRotation } from "@/features/cube/hooks/useCubeRotation";
import CubeModel from "./CubeModel";

// Orbit rotation is applied to this group; the model inside is drawn from
// engine state. Layer turning (pivot groups) arrives in a later PR.
export default function Cube({
  cube,
  setOrbitalControlsEnabled,
  rotationState,
}: CubeProps) {
  const cubeGroupRef = useCubeRotation(rotationState);
  return (
    <group ref={cubeGroupRef}>
      <CubeModel cube={cube} setOrbitalControlsEnabled={setOrbitalControlsEnabled} />
    </group>
  );
}
