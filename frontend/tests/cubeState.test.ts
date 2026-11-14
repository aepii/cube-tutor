import { rotateFaceMatrix } from "@/features/cube/helpers/cubeState";
import { FaceIndex } from "@/features/cube/types/cube.types";

describe("Cube State Math - 2D Matrix Rotation", () => {
  it("should rotate a 3x3 matrix 90 degrees clockwise", () => {
    const inputFace: FaceIndex[][] = [
      [1, 2, 3],
      [4, 5, 6],
      [7, 8, 9],
    ] as unknown as FaceIndex[][];

    const result = rotateFaceMatrix(inputFace, "CW");

    const expectedOutput = [
      [7, 4, 1],
      [8, 5, 2],
      [9, 6, 3],
    ];

    expect(result).toEqual(expectedOutput);
  });
});
