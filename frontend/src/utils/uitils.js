import { supabase } from "./supabaseClient";

// utility functions goes here
// Function to generate a random password
export const generateRandomPassword = (length = 12) => {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+~`|}{[]:;?><,./-=";
  let password = "";
  for (let i = 0; i < length; i++) {
    password += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return password;
};

export const getToken = async () => {
  const { data, error } = await supabase.auth.getSession();

  if (data?.session) {
    const token = data.session.access_token;
    return token;
  }

  // Fall back to refresh for cases where an access token has expired
  // but Supabase still holds a valid refresh session.
  const { data: refreshed, error: refreshError } =
    await supabase.auth.refreshSession();
  if (refreshed?.session?.access_token) {
    return refreshed.session.access_token;
  }

  if (error) console.error("Error fetching session:", error.message);
  if (refreshError)
    console.error("Error refreshing session:", refreshError.message);
  return null;
};
