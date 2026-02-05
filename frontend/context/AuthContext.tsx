import React, { createContext, useState, useEffect, useContext } from "react";
import { saveToken, getToken, removeToken } from "@/utils/storage";

interface AuthContextType {
  token: string | null;
  isLoading: boolean;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for token on application bootup
  useEffect(() => {
    const loadToken = async () => {
      const storedToken = await getToken("access_token");
      if (storedToken) {
        setToken(storedToken);
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
