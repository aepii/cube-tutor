import { CubeProps } from "@/features/cube/types/cube.types";
import { useCubeRotation } from "@/features/cube/hooks/useCubeRotation";
import { useCubeTurn } from "@/features/cube/hooks/useCubeTurn";
import { useCubieGeneration } from "@/features/cube/hooks/useCubieGeneration";
import Cubie from "./Cubie";

export default function Cube({
  cubeData,
  setOrbitalControlsEnabled,
  rotationState,
  turnInput,
  setTurnInput,
}: CubeProps) {
  const cubeGroupRef = useCubeRotation(rotationState);
  const pivotGroupRef = useCubeTurn(turnInput);
  const cubies = useCubieGeneration(cubeData);
  return (
    <group ref={cubeGroupRef}>
      {cubies.map(({ key, position, faceColors }) => (
        <Cubie
          key={key}
          position={position}
          faceColors={faceColors}
          setOrbitalControlsEnabled={setOrbitalControlsEnabled}
          setTurnInput={setTurnInput}
        />
      ))}
    </group>
  );
}
