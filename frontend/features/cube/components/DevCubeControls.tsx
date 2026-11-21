import { useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useCubeStore } from "@/features/cube/store/useCubeStore";

// Development-only overlay (rendered under __DEV__):
// - type an algorithm and Play it, animated with moves exactly as written
//   (R2' turns counter-clockwise, R3 turns 270°)
// - Scramble (animated, fast) and Reset
export default function DevCubeControls() {
  const playAlgorithm = useCubeStore((s) => s.playAlgorithm);
  const scramble = useCubeStore((s) => s.scramble);
  const reset = useCubeStore((s) => s.reset);
  const lastScramble = useCubeStore((s) => s.lastScramble);
  const nowPlaying = useCubeStore((s) =>
    s.activeTurn?.kind === "animate" ? (s.activeTurn.move?.notation ?? null) : null,
  );

  const [alg, setAlg] = useState("R U R' U'");
  const [error, setError] = useState<string | null>(null);

  const play = () => {
    try {
      playAlgorithm(alg);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <View style={styles.container} pointerEvents="box-none">
      {nowPlaying && <Text style={styles.now}>{nowPlaying}</Text>}
      {lastScramble && <Text style={styles.mono}>{lastScramble}</Text>}
      {error && <Text style={styles.error}>{error}</Text>}

      <View style={styles.row}>
        <TextInput
          style={styles.input}
          value={alg}
          onChangeText={setAlg}
          onSubmitEditing={play}
          autoCapitalize="none"
          autoCorrect={false}
          placeholder="R U R' U'"
          placeholderTextColor="#9ab"
        />
        <Pressable style={styles.button} onPress={play}>
          <Text style={styles.label}>Play</Text>
        </Pressable>
      </View>

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
  now: { color: "#ffffff", fontSize: 22, fontWeight: "700", fontFamily: "monospace" },
  mono: { color: "#ffffff", fontFamily: "monospace", fontSize: 13, textAlign: "center" },
  error: { color: "#ffb4b4", fontSize: 13 },
  row: { flexDirection: "row", gap: 12, alignItems: "center" },
  input: {
    minWidth: 200,
    color: "#ffffff",
    fontFamily: "monospace",
    backgroundColor: "rgba(0, 0, 0, 0.35)",
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  button: {
    backgroundColor: "rgba(0, 0, 0, 0.45)",
    paddingVertical: 10,
    paddingHorizontal: 18,
    borderRadius: 8,
  },
  label: { color: "#ffffff", fontWeight: "600" },
});
