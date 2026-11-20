import { FaceMove } from "@/features/cube/types/move.types";

const FACES: readonly FaceMove[] = ["R", "L", "U", "D", "F", "B"];
const MODIFIERS = ["", "'", "2"] as const;
const AXIS: Record<FaceMove, number> = { R: 0, L: 0, U: 1, D: 1, F: 2, B: 2 };

// Random-move scramble in standard notation, e.g. "R U2 F' L ...".
// Rules (as in WCA-style random-move scramblers):
// - never the same face twice in a row (R R' would cancel)
// - never three moves on the same axis in a row (R L R' is redundant)
// `random` is injectable so tests are deterministic.
export function randomScramble(
  length = 20,
  random: () => number = Math.random,
): string {
  const moves: FaceMove[] = [];
  const tokens: string[] = [];
  const pick = <T>(items: readonly T[]) => items[Math.floor(random() * items.length)];

  while (moves.length < length) {
    const face = pick(FACES);
    const last = moves[moves.length - 1];
    const secondLast = moves[moves.length - 2];

    if (face === last) continue;
    if (
      last !== undefined &&
      secondLast !== undefined &&
      AXIS[face] === AXIS[last] &&
      AXIS[face] === AXIS[secondLast]
    ) {
      continue;
    }

    moves.push(face);
    tokens.push(face + pick(MODIFIERS));
  }

  return tokens.join(" ");
}
