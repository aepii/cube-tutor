import { Pressable, StyleSheet, Text, View } from "react-native";
import { useCubeStore } from "@/features/cube/store/useCubeStore";

// Development-only overlay (rendered under __DEV__) to put the cube in a
// scrambled state until layer turning and algorithm playback exist.
// Moves apply instantly; animation comes with layer turning.
export default function DevCubeControls() {
  const scramble = useCubeStore((s) => s.scramble);
  const reset = useCubeStore((s) => s.reset);
  const lastScramble = useCubeStore((s) => s.lastScramble);

  return (
    <View style={styles.container} pointerEvents="box-none">
      {lastScramble && <Text style={styles.scramble}>{lastScramble}</Text>}
      <View style={styles.row}>
        <Pressable style={styles.button} onPress={scramble}>
          <Text style={styles.label}>Scramble</Text>
        </Pressable>
        <Pressable style={styles.button} onPress={reset}>
          <Text style={styles.label}>Reset</Text>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 24,
    alignItems: "center",
    gap: 8,
  },
  scramble: {
    color: "#ffffff",
    fontFamily: "monospace",
    fontSize: 13,
    textAlign: "center",
  },
  row: { flexDirection: "row", gap: 12 },
  button: {
    backgroundColor: "rgba(0, 0, 0, 0.45)",
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 8,
  },
  label: { color: "#ffffff", fontWeight: "600" },
});
