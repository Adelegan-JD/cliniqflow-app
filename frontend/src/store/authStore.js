import { create } from "zustand";
import { supabase } from "../utils/supabaseClient";
import { persist } from 'zustand/middleware';

export const useAuthStore = create(persist((set) => {
  return {
    isAuthenticated: false,
    user: null,
    loading: false,
    error: null,
    setError: (error) => set({ error }),
    login: async (userData) => {
      set({ loading: true });
      try {
        const { data, error } =
          await supabase.auth.signInWithPassword(userData);
        if (error) {
          throw new Error(error.message);
        } else {
          console.log("Login successful:", data.user);
          set({ isAuthenticated: true, user: data.user });
          // return the user object so callers can redirect based on role
          return data.user;
        }
      } catch (error) {
        set({
          error: error.message || "An unexpected error occurred during login.",
        });
        // rethrow so caller knows login failed
        throw error;
      } finally {
        set({ loading: false });
      }
    },

    logout: async () => {
      const { error } = await supabase.auth.signOut();
      set({ isAuthenticated: false, user: null });
    },
  };
}));
