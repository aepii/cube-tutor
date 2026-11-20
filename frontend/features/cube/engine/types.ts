// Coordinate system (matches the 3D view and three.js):
//   +X = Right, -X = Left, +Y = Up, -Y = Down, +Z = Front, -Z = Back.
// Cubie positions use integer coordinates in {-1, 0, 1}.

export type Vec3 = readonly [number, number, number];

export type Axis = 0 | 1 | 2; // x, y, z

// A sticker's color is identified by the face it sits on when the cube is solved.
// Same numbering as the renderer and the face-slot order (+X -X +Y -Y +Z -Z):
//   0 = R (red), 1 = L (orange), 2 = U (white), 3 = D (yellow), 4 = F (green), 5 = B (blue)
export type Color = 0 | 1 | 2 | 3 | 4 | 5;

export interface Sticker {
  // Position of the cubie this sticker belongs to
  readonly pos: Vec3;
  // Outward direction the sticker faces (a unit axis vector)
  readonly normal: Vec3;
  readonly color: Color;
}

// 54 stickers. A sticker keeps its array index forever; moves only change its
// pos and normal. That makes two equal cube states deep-equal (toEqual).
export type CubeState = readonly Sticker[];

// What a move does: rotate every sticker whose coordinate on `axis` is in
// `layers` by a quarter turn in direction `sign`.
// sign = +1 is +90° (counterclockwise looking from the + end of the axis),
// sign = -1 is -90° (clockwise looking from the + end of the axis).
export interface MoveSpec {
  readonly axis: Axis;
  readonly layers: readonly number[];
  readonly sign: 1 | -1;
}
