export const INPUT_CONSTANTS = {
  // Orbit: radians of cube rotation per pixel dragged on the background
  ORBIT_RADIANS_PER_PX: 0.008,

  // Turn: pixels a drag on a face must travel before the layer/axis is chosen
  TURN_START_PX: 10,
  // Drag distance across a face (cube units; 1 = one piece width) per quarter turn
  TURN_UNITS_PER_QUARTER: 1.2,

  // Zoom = camera distance multiplier (1 = default; larger = farther away)
  ZOOM_MIN: 0.6,
  ZOOM_MAX: 2.2,
  // Web mouse wheel: zoom factor per wheel pixel (exponential)
  WHEEL_ZOOM_PER_PX: 0.0015,

  // Turn animation: duration of a quarter turn; each further quarter adds
  // EXTRA_QUARTER_FACTOR of that (so a half turn isn't twice as slow)
  QUARTER_TURN_MS: 150,
  EXTRA_QUARTER_FACTOR: 0.6,
  // Scramble playback speed multiplier (20 moves in ~2 s)
  SCRAMBLE_SPEED: 2,
} as const;
