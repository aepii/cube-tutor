import axios from "axios";
import { getToken, removeToken } from "@/features/auth/utils/storage";
import { router } from "expo-router";

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
    const token = await getToken("access_token");
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
        await removeToken("access_token");
        router.replace("/(auth)/login");
      } catch (error) {
        console.error("Error clearing token on 401", error);
      }
    }
    return Promise.reject(error);
  },
);

export default api;
