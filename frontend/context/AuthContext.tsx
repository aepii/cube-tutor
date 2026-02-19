import React, { createContext, useState, useEffect, useContext } from "react";
import { jwtDecode } from "jwt-decode";
import { saveToken, getToken, removeToken } from "@/utils/storage";

interface AuthContextType {
  token: string | null;
  isLoading: boolean;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

interface DecodedJWT {
  sub: string;
  exp: number;
  type: "access" | "refresh";
}

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for token on application bootup
  useEffect(() => {
    const loadToken = async () => {
      const storedToken = await getToken("access_token");
      if (storedToken) {
        try {
          const decoded: DecodedJWT = jwtDecode(storedToken);
          const currentTime = Date.now() / 1000;
          if (currentTime > decoded.exp) {
            console.warn("Token expired");
            await removeToken("access_token");
            setToken(null);
          }
          setToken(storedToken);
        } catch (e) {
          console.error("Invalid token format", e);
          await removeToken("access_token");
          setToken(null);
        }
      }
      setIsLoading(false);
    };
    loadToken();
  }, []);

  // Save token
  const signIn = async (newToken: string) => {
    setToken(newToken);
    await saveToken("access_token", newToken);
  };

  // Remove token
  const signOut = async () => {
    setToken(null);
    await removeToken("access_token");
  };

  return (
    <AuthContext.Provider value={{ token, isLoading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
