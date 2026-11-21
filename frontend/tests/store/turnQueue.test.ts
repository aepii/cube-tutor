import { applyAlgorithm, createSolvedCube } from "@/features/cube/engine";
import { parseAlgorithm } from "@/features/cube/helpers/moveParser";
import { isBusy, turnAngle, useCubeStore } from "@/features/cube/store/useCubeStore";

const store = () => useCubeStore.getState();
const expected = (alg: string) => applyAlgorithm(createSolvedCube(), parseAlgorithm(alg));

// Stand-in for the renderer: finish every animation until the queue is empty
function runAnimations() {
  let guard = 0;
  while (store().activeTurn && guard++ < 1000) store().finishTurn();
}

beforeEach(() => store().reset());

describe("algorithm playback", () => {
  it("animates moves one at a time and ends in the same state as applyAlgorithm", () => {
    store().playAlgorithm("R U R' U' R2' F3");
    expect(store().activeTurn?.move?.notation).toBe("R");
    expect(store().queue).toHaveLength(5);
    runAnimations();
    expect(store().cube).toEqual(expected("R U R' U' R2' F3"));
    expect(isBusy(store())).toBe(false);
  });

  it("keeps the literal angle of each move (R2' counter-clockwise, R3 270°)", () => {
    store().playAlgorithm("R2'");
    expect(store().activeTurn?.toAngle).toBeCloseTo(Math.PI);
    store().reset();
    store().playAlgorithm("R3");
    expect(store().activeTurn?.toAngle).toBeCloseTo((-3 * Math.PI) / 2);
  });

  it("(R U R' U') x6 returns to solved", () => {
    store().playAlgorithm("R U R' U' ".repeat(6));
    runAnimations();
    expect(store().cube).toEqual(createSolvedCube());
  });

  it("queues moves added while a turn is playing", () => {
    store().playAlgorithm("R");
    store().playAlgorithm("U");
    expect(store().queue.map((q) => q.move.notation)).toEqual(["U"]);
    runAnimations();
    expect(store().cube).toEqual(expected("R U"));
  });
});

describe("drag turns", () => {
  it("a drag released under 45° snaps back without changing the state", () => {
    expect(store().startDragTurn(0, 1)).toBe(true);
    turnAngle.current = -0.4;
    store().releaseDragTurn();
    expect(store().activeTurn?.move).toBeNull();
    expect(store().activeTurn?.toAngle).toBe(0);
    runAnimations();
    expect(store().cube).toEqual(createSolvedCube());
  });

  it("a drag released past 45° commits a quarter turn", () => {
    store().startDragTurn(0, 1);
    turnAngle.current = -1.0; // about -57° about +x = R
    store().releaseDragTurn();
    expect(store().activeTurn?.move?.notation).toBe("R");
    runAnimations();
    expect(store().cube).toEqual(expected("R"));
  });

  it("a drag released past 135° commits a half turn", () => {
    store().startDragTurn(0, 1);
    turnAngle.current = -2.5; // about -143°
    store().releaseDragTurn();
    expect(store().activeTurn?.move?.notation).toBe("R2");
    runAnimations();
    expect(store().cube).toEqual(expected("R2"));
  });

  it("can't start while a move is playing", () => {
    store().playAlgorithm("R");
    expect(store().startDragTurn(1, 1)).toBe(false);
  });
});

describe("scramble / reset", () => {
  it("scramble plays the shown scramble", () => {
    store().scramble();
    const scramble = store().lastScramble!;
    expect(isBusy(store())).toBe(true);
    runAnimations();
    expect(store().cube).toEqual(expected(scramble));
  });

  it("reset stops playback and returns to solved", () => {
    store().playAlgorithm("R U F");
    store().reset();
    expect(isBusy(store())).toBe(false);
    expect(store().cube).toEqual(createSolvedCube());
  });
});
