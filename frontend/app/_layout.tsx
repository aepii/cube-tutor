import { Slot, useRouter, useSegments } from "expo-router";
import { useEffect } from "react";
import { useAuthStore } from "@/features/auth/store/useAuthStore";
import { View, ActivityIndicator } from "react-native";

export default function RootLayout() {
  const { token, isLoading, checkToken } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  // Run token check
  useEffect(() => {
    checkToken();
  }, []);

  // Handle authentication routing
  useEffect(() => {
    if (isLoading) return;

    // Check if in auth screens
    const inAuthGroup = segments[0] === "(auth)";

    if (!token && !inAuthGroup) {
      // If not logged in and not in auth screens, go to login
      router.replace("/(auth)/login");
    } else if (token && inAuthGroup) {
      // If logged in and trying to access auth screens, go to tabs
      router.replace("/(tabs)/playground");
    }
  }, [token, isLoading, segments]);

  return (
    <>
      <Slot />
      {isLoading && (
        <View>
          <ActivityIndicator />
        </View>
      )}
    </>
  );
}
