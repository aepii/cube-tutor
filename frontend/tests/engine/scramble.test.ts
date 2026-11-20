import { randomScramble } from "@/features/cube/engine";
import { parseAlgorithm } from "@/features/cube/helpers/moveParser";

// Deterministic pseudo-random sequence for repeatable tests
function seeded(seed: number) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}

const AXIS: Record<string, number> = { R: 0, L: 0, U: 1, D: 1, F: 2, B: 2 };

describe("randomScramble", () => {
  it("produces 20 face moves by default, all parseable", () => {
    const moves = parseAlgorithm(randomScramble(20, seeded(1)));
    expect(moves).toHaveLength(20);
    for (const m of moves) {
      expect("RLUDFB").toContain(m.base);
      expect([1, -1, 2]).toContain(m.turns);
    }
  });

  it("respects a custom length", () => {
    expect(parseAlgorithm(randomScramble(7, seeded(2)))).toHaveLength(7);
  });

  it.each([1, 2, 3, 4, 5, 42, 1234])(
    "seed %i: never repeats a face or uses one axis three times in a row",
    (seed) => {
      const bases = parseAlgorithm(randomScramble(40, seeded(seed))).map((m) => m.base);
      for (let i = 1; i < bases.length; i++) {
        expect(bases[i]).not.toBe(bases[i - 1]);
        if (i >= 2) {
          const sameAxis =
            AXIS[bases[i]] === AXIS[bases[i - 1]] && AXIS[bases[i]] === AXIS[bases[i - 2]];
          expect(sameAxis).toBe(false);
        }
      }
    },
  );

  it("is deterministic for a given random source", () => {
    expect(randomScramble(20, seeded(9))).toBe(randomScramble(20, seeded(9)));
  });
});
