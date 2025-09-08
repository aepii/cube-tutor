import { CubeProps } from "@/types";
import { useCubeRotation, useCubeTurn, useCubieGeneration } from "@/hooks";
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
