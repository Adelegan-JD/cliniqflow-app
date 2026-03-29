import { create } from "zustand";
import { api } from "../utils/api";

const useNurseStore = create((set) => {
    return {
        health: null,
        isLoading: false,
        gethealthStatus: async () => {
            try {
                set({ isLoading: true });
                const data = await api.get("/health");
                set({ health: data, isLoading: false });
            } catch (error) {
                set({ isLoading: false });
            }
        }
    }
})

export { useNurseStore };