import axios from "axios";
import { router } from "expo-router";
import { useAuthStore } from "@/features/auth/store/useAuthStore";
import { getToken } from "@/features/auth/utils/storage";

const API_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach access token to every request
api.interceptors.request.use(
  async (config) => {
    let token = useAuthStore.getState().token;
    if (!token) {
      token = await getToken("access_token");
    }
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// Check for unauthorized error and redirect to login
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        useAuthStore.getState().signOut();
        router.replace("/(auth)/login");
      } catch (error) {
        console.error("Error clearing token on 401", error);
      }
    }
    return Promise.reject(error);
  },
);

export default api;
