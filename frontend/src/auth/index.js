/**
 * Authentication Context
 * Provides authentication state to the entire app
 */

import React, { createContext, useState, useCallback, useEffect } from "react";
import { authService } from "./authService";

export const AuthContext = createContext({
  isAuthenticated: false,
  user: null,
  login: async () => false,
  logout: () => {},
});

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState(authService.getAuthState());

  useEffect(() => {
    // Subscribe to auth state changes
    const unsubscribe = authService.subscribe(setAuthState);
    return unsubscribe;
  }, []);

  const login = useCallback(async (email, password) => {
    return await authService.login(email, password);
  }, []);

  const logout = useCallback(() => {
    authService.logout();
  }, []);

  const value = {
    isAuthenticated: authState.isAuthenticated,
    user: authState.user,
    token: authState.token,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
