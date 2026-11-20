// Geometry of the rendered cube. Pieces sit on an integer grid (spacing 1),
// so sizes below are fractions of one piece.
export const RENDER_CONSTANTS = {
  // Each piece is one rounded box of colored plastic (stickerless, like modern
  // GAN / MoYu cubes). The small gap between pieces shows the internal color.
  PIECE_SIZE: 1,
  PIECE_RADIUS: 0.085,
  PIECE_SEGMENTS: 5,
} as const;
