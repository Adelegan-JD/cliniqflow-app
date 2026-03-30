import { create } from "zustand";
import { api } from "../utils/api";

const useAdminStore = create((set) => {
  return {
    users: [],
    isLoading: false,
    error: null,
    adminError: null,
    reset: () => set({users: [], isLoading: false, error: null, adminError: null}),
    setUsers: (users) => set({ users }),
    addUser: (user) => set((state) => ({ users: [...state.users, user] })),
    removeUser: (userId) =>
      set((state) => ({ users: state.users.filter((u) => u.id !== userId) })),
    updateUser: (updatedUser) =>
      set((state) => ({
        users: state.users.map((u) =>
          u.id === updatedUser.id ? updatedUser : u,
        ),
      })),
    fetchUsers: async () => {
      try {
        set({ isLoading: true, error: null, adminError: null });
        const data = await api.get("/admin/users");
        // API expected to return an array of users directly
        let usersArray = Array.isArray(data) ? data : data.users || [];
        // normalize shape: backend returns { name, role, email }
        // ensure `name`/`email` exist for older entries
        usersArray = usersArray.map((u) => ({
          ...u,
          name: u.name || u.display_name || u.email || "",
          email: u.email || "",
        }));
        set({ users: usersArray });
      } catch (err) {
        console.error("fetchUsers failed", err);
        const message =
          err.message || "An unexpected error occurred while fetching users.";
        set({
          error: message,
          adminError: "Unable to reach admin service. Try again later.",
        });
        // leave any previous users intact so that UI doesn't blank out
      } finally {
        set({ isLoading: false });
      }
    },
  };
});

export { useAdminStore };
