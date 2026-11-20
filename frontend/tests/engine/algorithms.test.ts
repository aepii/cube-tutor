import fs from "fs";
import path from "path";
import {
  createSolvedCube,
  applyAlgorithm,
  isSolved,
  isF2LSolved,
  isLastLayerOriented,
} from "@/features/cube/engine";
import { parseAlgorithm } from "@/features/cube/helpers/moveParser";

type RawSubset = {
  subset: string;
  cases: {
    name: string;
    setup: string;
    solutions: { orientation: string; alg: string }[];
  }[];
};

const load = (name: string): RawSubset =>
  JSON.parse(
    fs.readFileSync(
      path.join(__dirname, "../../../shared/data/raw", `${name}.json`),
      "utf-8",
    ),
  );

const run = (alg: string) => applyAlgorithm(createSolvedCube(), parseAlgorithm(alg));

// Possible top-layer adjustments ("AUF") before and after the algorithm
const AUF = ["", "U", "U2", "U'"];

describe("PLL: every solution solves its case (allowing a U turn before and after)", () => {
  const rows = load("pll").cases.flatMap((c) =>
    c.solutions.map((s) => [c.name, s.alg, c.setup] as const),
  );

  test.each(rows)("%s: %s", (_name, alg, setup) => {
    const solves = AUF.some((pre) =>
      AUF.some((post) => isSolved(run(`${setup} ${pre} ${alg} ${post}`))),
    );
    expect(solves).toBe(true);
  });
});

describe("OLL: every solution orients the last layer of its case (allowing a U turn before)", () => {
  const rows = load("oll").cases.flatMap((c) =>
    c.solutions.map((s) => [c.name, s.alg, c.setup] as const),
  );

  test.each(rows)("%s: %s", (_name, alg, setup) => {
    const orients = AUF.some((pre) => isLastLayerOriented(run(`${setup} ${pre} ${alg}`)));
    expect(orients).toBe(true);
  });
});

// The F2L setups put the case in the front-right slot. Solutions for the other
// slots (orientation 1-3) are checked by moving the setup to that slot with a
// whole-cube y rotation: rotate, set up the case in the new front-right, rotate back.
const SLOT_CONJUGATES: Record<string, [string, string]> = {
  "0": ["", ""], // front right
  "1": ["y'", "y"], // front left
  "2": ["y2", "y2"], // back left
  "3": ["y", "y'"], // back right
};

describe("F2L: every solution solves the first two layers (allowing a U turn before)", () => {
  const rows = load("f2l").cases.flatMap((c) =>
    c.solutions.map((s) => [c.name, s.orientation, s.alg, c.setup] as const),
  );

  test.each(rows)("%s (slot %s): %s", (_name, orientation, alg, setup) => {
    const [before, after] = SLOT_CONJUGATES[orientation];
    const caseState = `${before} ${setup} ${after}`;
    const solves = AUF.some((pre) => isF2LSolved(run(`${caseState} ${pre} ${alg}`)));
    expect(solves).toBe(true);
  });
});

// Guards against the checks above passing trivially: every setup must actually
// produce an unsolved case, whatever the U-layer adjustment.
describe("setups really scramble their case", () => {
  it.each(load("pll").cases.map((c) => [c.name, c.setup]))("PLL %s", (_name, setup) => {
    const solved = AUF.some((pre) =>
      AUF.some((post) => isSolved(run(`${setup} ${pre} ${post}`))),
    );
    expect(solved).toBe(false);
  });

  it.each(load("oll").cases.map((c) => [c.name, c.setup]))("OLL %s", (_name, setup) => {
    expect(AUF.some((pre) => isLastLayerOriented(run(`${setup} ${pre}`)))).toBe(false);
  });

  it.each(load("f2l").cases.map((c) => [c.name, c.setup]))("F2L %s", (_name, setup) => {
    expect(AUF.some((pre) => isF2LSolved(run(`${setup} ${pre}`)))).toBe(false);
  });
});
