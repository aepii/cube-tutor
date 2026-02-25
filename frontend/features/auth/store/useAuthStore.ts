import { create } from "zustand";
import { jwtDecode } from "jwt-decode";
import {
  saveToken,
  getToken,
  removeToken,
} from "@/features/auth/utils/storage";

interface DecodedJWT {
  sub: string;
  exp: number;
  type: "access" | "refresh";
}

interface AuthState {
  token: string | null;
  isLoading: boolean;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
  checkToken: () => Promise<void>;
}
export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  isLoading: true,

  checkToken: async () => {
    const storedToken = await getToken("access_token");
    if (storedToken) {
      try {
        const decoded: DecodedJWT = jwtDecode(storedToken);
        const currentTime = Date.now() / 1000;
        if (currentTime > decoded.exp) {
          console.warn("Token expired");
          await removeToken("access_token");
          set({ token: null, isLoading: false });
        } else {
          set({ token: storedToken, isLoading: false });
        }
      } catch (e) {
        console.error("Invalid token format", e);
        await removeToken("access_token");
        set({ token: null, isLoading: false });
      }
    } else {
      set({ isLoading: false });
    }
  },

  signIn: async (newToken: string) => {
    console.log(newToken);
    await saveToken("access_token", newToken);
    set({ token: newToken });
  },

  signOut: async () => {
    await removeToken("access_token");
    set({ token: null });
  },
}));
