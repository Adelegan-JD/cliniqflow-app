import { create } from "zustand";
import { supabase } from "../utils/supabaseClient";
import { persist } from "zustand/middleware";

export const useAuthStore = create(
  persist((set) => {
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
            // CRITICAL: signInWithPassword doesn't populate user_metadata.
            // Call getUser() to fetch the full user object with metadata.
            const {
              data: { user: freshUser },
            } = await supabase.auth.getUser();
            const userToStore = freshUser || data.user;
            set({ isAuthenticated: true, user: userToStore });
            return userToStore;
          }
        } catch (error) {
          set({
            error:
              error.message || "An unexpected error occurred during login.",
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
  }),
);
