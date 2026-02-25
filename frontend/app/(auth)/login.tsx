import { useState } from "react";
import { View, TextInput, Button, Text } from "react-native";
import { useRouter, Link } from "expo-router";
import { useAuthStore } from "@/features/auth/store/useAuthStore";
import { loginUser } from "@/features/auth/services/auth.service";
import { globalStyles as styles } from "@/shared/styles/globalStyles";

export default function LoginScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { signIn } = useAuthStore();
  const router = useRouter();

  const handleLogin = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await loginUser(username, password);
      await signIn(data.access_token);
    } catch (err: any) {
      console.error(err);

      const detail = err.response?.data?.detail;

      // Pydantic error
      if (Array.isArray(detail)) {
        setError(detail[0].msg);
      } else if (typeof detail === "string") {
        setError(detail);
      } else {
        setError("An unexpected error occured");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>CubeTutor Login</Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <TextInput
        style={styles.input}
        placeholder="Username"
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
      />

      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoCapitalize="none"
      />

      <Button
        title={loading ? "Logging in..." : "Login"}
        onPress={handleLogin}
        disabled={loading}
      />

      <View style={styles.footer}>
        <Text>Don't have an account? </Text>
        <Link href="/(auth)/register">
          <Text style={{ color: "blue" }}>Register</Text>
        </Link>
      </View>
    </View>
  );
}
