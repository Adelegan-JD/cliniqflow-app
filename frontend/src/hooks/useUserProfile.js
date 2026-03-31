import { useAuth } from "../contexts/AuthContext";

/**
 * Get the current user's display profile from auth.
 * Name comes from user_metadata (set when admin creates user) or email fallback.
 */
export function useUserProfile() {
  const { user } = useAuth();
  const meta = user?.user_metadata || {};
  const displayName =
    meta.display_name || meta.name || user?.email?.split("@")[0] || "User";
  const role =
    meta.role === "record_officer"
      ? "Record Officer"
      : meta.role
        ? String(meta.role)[0].toUpperCase() + String(meta.role).slice(1).replace("_", " ")
        : "User";
  return {
    name: displayName,
    role,
    email: user?.email,
    avatar: user?.user_metadata?.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}&background=random`,
  };
}
