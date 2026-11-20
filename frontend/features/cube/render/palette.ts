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

// Plastic core visible in the seams between tiles
export const CORE_COLOR = "#141414";

// How strongly a touched tile glows (fraction of its own color)
export const HIGHLIGHT_EMISSIVE_INTENSITY = 0.35;
