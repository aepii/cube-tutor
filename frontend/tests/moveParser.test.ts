import { parseAlgorithm } from "@/features/cube/helpers/moveParser";

describe("parseAlgorithm", () => {
  it("parses basic moves", () => {
    expect(parseAlgorithm("R U R' U'")).toEqual([
      { base: "R", modifier: "" },
      { base: "U", modifier: "" },
      { base: "R", modifier: "'" },
      { base: "U", modifier: "'" },
    ]);
  });

  it("parses lowercase wide moves", () => {
    expect(parseAlgorithm("r' f2")).toEqual([
      { base: "r", modifier: "'" },
      { base: "f", modifier: "2" },
    ]);
  });

  it("treats Rw as r", () => {
    expect(parseAlgorithm("Rw2")).toEqual([{ base: "r", modifier: "2" }]);
  });

  it("normalizes 2' to 2", () => {
    expect(parseAlgorithm("U2'")).toEqual([{ base: "U", modifier: "2" }]);
  });

  it("ignores parentheses and extra spaces", () => {
    expect(parseAlgorithm(" (R U)  R' ")).toHaveLength(3);
  });

  it("rejects unknown moves", () => {
    expect(() => parseAlgorithm("R Q")).toThrow();
  });
});
