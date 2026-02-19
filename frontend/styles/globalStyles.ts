import { StyleSheet } from "react-native";
import { colors } from "@/theme/colors";

export const globalStyles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    padding: 20,
    backgroundColor: colors.background,
  },
  header: { fontSize: 24, marginBottom: 10, textAlign: "center" },
  input: {
    borderWidth: 1,
    borderColor: colors.border,
    padding: 10,
    borderRadius: 5,
  },
  error: { color: colors.error, marginBottom: 10 },
  footer: { marginTop: 20, flexDirection: "row", justifyContent: "center" },
});
