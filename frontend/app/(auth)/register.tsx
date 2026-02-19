import { useState } from "react";
import { View, TextInput, Button, Text } from "react-native";
import { useRouter, Link } from "expo-router";
import { useAuth } from "@/context/AuthContext";
import { registerUser } from "@/services/auth.service";
import { globalStyles as styles } from "@/styles/globalStyles";

export default function RegisterScreen() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const { signIn } = useAuth();
  const router = useRouter();

  const handleRegister = async () => {
    setLoading(true);
    setError("");

    try {
      const data = await registerUser(email, username, password);
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
      <Text style={styles.header}>CubeTutor Register</Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        inputMode="email"
      />

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
        title={loading ? "Signing up..." : "Register"}
        onPress={handleRegister}
        disabled={loading}
      />

      <View style={styles.footer}>
        <Text>Already have an account? </Text>
        <Link href="/(auth)/login">
          <Text style={{ color: "blue" }}>Login</Text>
        </Link>
      </View>
    </View>
  );
}
