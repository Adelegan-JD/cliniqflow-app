import { createContext, useContext, useEffect, useState } from "react";
// import { Session, User } from "@supabase/supabase-js";
import { supabase } from "../utils/supabaseClient";

const AuthContext = createContext(undefined);

export const AuthProvider = ({ children }) => {

  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Check active session on load
    (async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);

      // If there's a stored auth token but no valid session, sign out and redirect to root
      const auth_token = localStorage.getItem("AUTH_TOKEN_KEY");
      if (auth_token && !session?.access_token) {
        await supabase.auth.signOut();
        localStorage.removeItem("AUTH_TOKEN_KEY");
        setSession(null);
        setUser(null);
        window.location.href = "/";
      }
    })();

    // 2. Listen for changes (Login, Logout, Auto-Refresh)
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === "PASSWORD_RECOVERY") {
        return;
      }

      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);

      const auth_token = localStorage.getItem("AUTH_TOKEN_KEY");
      if (auth_token && !session?.access_token) {
        // token was present but session is invalid/expired
        supabase.auth.signOut();
        localStorage.removeItem("AUTH_TOKEN_KEY");
        setSession(null);
        setUser(null);
        window.location.href = "/";
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const signOut = async () => {
    await supabase.auth.signOut();
    setSession(null);
    setUser(null);
    localStorage.removeItem("AUTH_TOKEN_KEY");
    window.location.href = "/";
  };

  const value = {
    session,
    user,
    loading,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
