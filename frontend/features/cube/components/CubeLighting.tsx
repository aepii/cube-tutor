import { LIGHTING_CONSTANTS as L } from "@/features/cube/constants/lighting.constants";

// Lights are fixed in world space (they don't rotate with the cube), so faces
// shade differently as you orbit, which is what makes the cube read as 3D.
export default function CubeLighting() {
  return (
    <>
      <ambientLight intensity={L.AMBIENT_INTENSITY} />
      <hemisphereLight
        args={[L.HEMISPHERE_SKY, L.HEMISPHERE_GROUND, L.HEMISPHERE_INTENSITY]}
      />
      <directionalLight position={L.KEY_POSITION} intensity={L.KEY_INTENSITY} />
      <directionalLight position={L.FILL_POSITION} intensity={L.FILL_INTENSITY} />
    </>
  );
}
