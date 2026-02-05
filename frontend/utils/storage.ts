import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

// Check if we are on the web
const isWeb = Platform.OS === "web";

// Saves token to location dependent on platform
export const saveToken = async (key: string, value: string) => {
  if (isWeb) {
    localStorage.setItem(key, value);
  } else {
    await SecureStore.setItemAsync(key, value);
  }
};

// Retrieves token from location dependent on platform
export const getToken = async (key: string) => {
  if (isWeb) {
    return localStorage.getItem(key);
  } else {
    return await SecureStore.getItemAsync(key);
  }
};

// Deletes token from location dependent on platform
export const removeToken = async (key: string) => {
  if (isWeb) {
    localStorage.removeItem(key);
  } else {
    await SecureStore.deleteItemAsync(key);
  }
};
