import { create } from "zustand";
import {
  Axis,
  CubeState,
  MOVE_TABLE,
  applyMove,
  createSolvedCube,
  randomScramble,
} from "@/features/cube/engine";
import { parseAlgorithm } from "@/features/cube/helpers/moveParser";
import {
  literalAngle,
  moveFor,
  snapQuarters,
  turnDurationMs,
} from "@/features/cube/helpers/turnMath";
import { Move } from "@/features/cube/types/move.types";
import { FaceRef } from "@/features/cube/types/input.types";
import { INPUT_CONSTANTS } from "@/features/cube/constants/input.constants";

// The layer currently turning. "drag": following the finger (angle comes from
// `turnAngle`); "animate": easing from `fromAngle` to `toAngle`, then `move`
// (if any) is applied to the cube state.
export interface ActiveTurn {
  id: number;
  axis: Axis;
  layers: readonly number[];
  kind: "drag" | "animate";
  move: Move | null;
  fromAngle: number;
  toAngle: number;
  durationMs: number;
}

interface QueuedMove {
  move: Move;
  speed: number;
}

// Live angle (radians about the turn's +axis) while dragging. Kept outside
// React state so a drag doesn't re-render at 60 fps; the renderer reads it
// every frame.
export const turnAngle = { current: 0 };

let nextTurnId = 1;

function animateMove({ move, speed }: QueuedMove): ActiveTurn {
  const spec = MOVE_TABLE[move.base];
  const toAngle = literalAngle(move);
  return {
    id: nextTurnId++,
    axis: spec.axis,
    layers: spec.layers,
    kind: "animate",
    move,
    fromAngle: 0,
    toAngle,
    durationMs: turnDurationMs(toAngle, speed),
  };
}

interface CubeStore {
  // Engine state: 54 stickers. The renderer draws directly from this.
  cube: CubeState;
  // The last scramble applied, for display (null when reset)
  lastScramble: string | null;
  queue: QueuedMove[];
  activeTurn: ActiveTurn | null;
  // Face glowing under the pointer / finger
  highlight: FaceRef | null;

  // Animated playback, moves exactly as written (R2' turns counter-clockwise)
  playAlgorithm: (alg: string) => void;
  enqueueMoves: (moves: Move[], speed?: number) => void;
  // Starts following the finger on a layer. false if the cube is busy.
  startDragTurn: (axis: Axis, layer: number) => boolean;
  // Snaps the dragged layer to the nearest quarter turn (or back to 0)
  releaseDragTurn: () => void;
  // Called by the renderer when an animation ends: applies the move and
  // starts the next queued one, in a single state update (no flicker)
  finishTurn: () => void;
  // Resets, then plays a random 20-move scramble quickly
  scramble: () => void;
  reset: () => void;
  setHighlight: (face: FaceRef | null) => void;
}

export const isBusy = (s: Pick<CubeStore, "activeTurn" | "queue">) =>
  s.activeTurn !== null || s.queue.length > 0;

export const useCubeStore = create<CubeStore>((set, get) => ({
  cube: createSolvedCube(),
  lastScramble: null,
  queue: [],
  activeTurn: null,
  highlight: null,

  playAlgorithm: (alg) => {
    get().enqueueMoves(parseAlgorithm(alg));
  },

  enqueueMoves: (moves, speed = 1) => {
    if (moves.length === 0) return;
    const queue = [...get().queue, ...moves.map((move) => ({ move, speed }))];
    if (get().activeTurn) {
      set({ queue });
    } else {
      turnAngle.current = 0;
      set({ activeTurn: animateMove(queue[0]), queue: queue.slice(1) });
    }
  },

  startDragTurn: (axis, layer) => {
    if (isBusy(get())) return false;
    turnAngle.current = 0;
    set({
      activeTurn: {
        id: nextTurnId++,
        axis,
        layers: [layer],
        kind: "drag",
        move: null,
        fromAngle: 0,
        toAngle: 0,
        durationMs: 0,
      },
    });
    return true;
  },

  releaseDragTurn: () => {
    const turn = get().activeTurn;
    if (!turn || turn.kind !== "drag") return;
    const angle = turnAngle.current;
    const quarters = snapQuarters(angle);
    const toAngle = quarters * (Math.PI / 2);
    set({
      activeTurn: {
        ...turn,
        kind: "animate",
        move: moveFor(turn.axis, turn.layers[0], quarters),
        fromAngle: angle,
        toAngle,
        durationMs: turnDurationMs(toAngle - angle),
      },
    });
  },

  finishTurn: () => {
    const { activeTurn, cube, queue } = get();
    if (!activeTurn) return;
    turnAngle.current = 0;
    set({
      cube: activeTurn.move ? applyMove(cube, activeTurn.move) : cube,
      activeTurn: queue.length > 0 ? animateMove(queue[0]) : null,
      queue: queue.slice(1),
    });
  },

  scramble: () => {
    const scramble = randomScramble();
    turnAngle.current = 0;
    set({ cube: createSolvedCube(), queue: [], activeTurn: null, lastScramble: scramble });
    get().enqueueMoves(parseAlgorithm(scramble), INPUT_CONSTANTS.SCRAMBLE_SPEED);
  },

  reset: () => {
    turnAngle.current = 0;
    set({
      cube: createSolvedCube(),
      queue: [],
      activeTurn: null,
      lastScramble: null,
      highlight: null,
    });
  },

  setHighlight: (face) => {
    const current = get().highlight;
    if (current?.pieceKey === face?.pieceKey && current?.slot === face?.slot) return;
    set({ highlight: face });
  },
}));
