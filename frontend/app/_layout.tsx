import { Slot, useRouter, useSegments } from "expo-router";
import { useEffect } from "react";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { View, ActivityIndicator } from "react-native";

const MainLayout = () => {
  const { token, isLoading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  // Handle authentication routing
  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === "(auth)";

    if (!token && !inAuthGroup) {
      // If not loggined and not in auth screens, go to login
      router.replace("/(auth)/login");
    } else if (token && inAuthGroup) {
      // If logged in and trying to access auth screens, go to tabs
      router.replace("/(tabs)/playground");
    }
  }, [token, isLoading, segments]);

  if (isLoading) {
    return (
      <View>
        <ActivityIndicator />
      </View>
    );
  }

  return <Slot />;
};

export default function RootLayout() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}
