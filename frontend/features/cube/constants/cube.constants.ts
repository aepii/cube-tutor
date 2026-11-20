// Geometry of the rendered cube. Cubies sit on an integer grid (spacing 1),
// so sizes below are fractions of one cubie.
export const RENDER_CONSTANTS = {
  // Dark rounded core of each piece; the gap between cores shows as dark seams
  CORE_SIZE: 0.96,
  CORE_RADIUS: 0.09,
  CORE_SEGMENTS: 4,

  // Colored rounded tile on each outer face (stickerless look)
  TILE_SIZE: 0.9, // final width including the bevel
  TILE_RADIUS: 0.12,
  TILE_DEPTH: 0.012,
  TILE_BEVEL: 0.012,
  TILE_BEVEL_SEGMENTS: 3,
  TILE_CURVE_SEGMENTS: 8,
} as const;

// Distance from a cubie's center to the outer surface of its core
export const CORE_HALF = RENDER_CONSTANTS.CORE_SIZE / 2;
