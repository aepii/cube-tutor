export const CAMERA_CONSTANTS = {
  DEFAULT_POSITION: [0, 0, 7.5] as [number, number, number],
  // Starting orientation of the cube (radians, Euler "XYZ": the Y turn is
  // applied first, then the X tilt). Shows Front, Right and Up in a
  // three-quarter view instead of a flat front face.
  INITIAL_TILT: { x: 0.5, y: -0.6 },
};

// Initial zoom (camera distance multiplier)
export const GESTURE_ZOOM_DEFAULT = 1;
