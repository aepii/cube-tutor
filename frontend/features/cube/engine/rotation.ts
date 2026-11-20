import { Axis, Vec3 } from "./types";

// Negate without producing -0, so states stay deep-equal under Jest's toEqual
// (which tells 0 and -0 apart).
const neg = (n: number) => 0 - n;

// Rotates an integer vector a quarter turn around a coordinate axis.
// sign = +1: +90° (right-hand rule), sign = -1: -90°.
export function rotateQuarter(v: Vec3, axis: Axis, sign: 1 | -1): Vec3 {
  const [x, y, z] = v;
  if (axis === 0) {
    return sign === 1 ? [x, neg(z), y] : [x, z, neg(y)];
  }
  if (axis === 1) {
    return sign === 1 ? [z, y, neg(x)] : [neg(z), y, x];
  }
  return sign === 1 ? [neg(y), x, z] : [y, neg(x), z];
}
