import { CubeProps } from "@/types";
import { useCubeRotation, useCubieGeneration } from "@/hooks";
import Cubie from "./Cubie";

export default function Cube({
  cubeData,
  setOrbitalControlsEnabled,
  rotationState,
}: CubeProps) {
  const cubeGroupRef = useCubeRotation(rotationState);
  const cubies = useCubieGeneration(cubeData);

  return (
    <group ref={cubeGroupRef}>
      {cubies.map(({ key, position, faceColors }) => (
        <Cubie
          key={key}
          position={position}
          faceColors={faceColors}
          setOrbitalControlsEnabled={setOrbitalControlsEnabled}
        />
      ))}
    </group>
  );
}
