import { Color } from "@/features/cube/engine";

// Speedcube palette, indexed by engine Color (0 = R ... 5 = B).
// Softer than pure RGB so the faces read well under lighting.
export const STICKER_COLORS: Record<Color, string> = {
  0: "#c41e3a", // red    (R)
  1: "#ff5800", // orange (L)
  2: "#ffffff", // white  (U)
  3: "#ffd500", // yellow (D)
  4: "#009e60", // green  (F)
  5: "#0051ba", // blue   (B)
};

// Internal plastic: the inner faces of pieces, visible only in the seams and
// mid-turn. Dark like most stickerless speedcubes ("#f2f2f2" for a white core).
export const INTERNAL_COLOR = "#141414";

// How strongly a touched face glows (fraction of its own color)
export const HIGHLIGHT_EMISSIVE_INTENSITY = 0.35;
