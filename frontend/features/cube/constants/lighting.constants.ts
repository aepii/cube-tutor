// Studio-style lighting: soft fill everywhere so no face goes black, a key light
// for shading and highlights on the rounded edges, and a dimmer fill from the
// opposite side. No environment maps (they can't be loaded reliably on native).
export const LIGHTING_CONSTANTS = {
  AMBIENT_INTENSITY: 0.45,

  HEMISPHERE_SKY: "#ffffff",
  HEMISPHERE_GROUND: "#3a3a3a",
  HEMISPHERE_INTENSITY: 0.6,

  KEY_POSITION: [4, 6, 5] as [number, number, number],
  KEY_INTENSITY: 1.6,

  FILL_POSITION: [-5, -2, -4] as [number, number, number],
  FILL_INTENSITY: 0.55,
} as const;
