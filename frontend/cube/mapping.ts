import { FaceIndex, FaceString } from "./types";
import { FACE_MAP, FACE_COLOR_MAP } from "./constants";

// Converts a face index to its corresponding face string
export const faceIndexToFaceString = (faceIndex: FaceIndex): FaceString => {
  return FACE_MAP[faceIndex];
};

// Converts a face index to its corresponding color
export const faceIndexToFaceColor = (faceIndex: FaceIndex): string => {
  return FACE_COLOR_MAP[faceIndex];
};
