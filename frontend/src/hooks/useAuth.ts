import { useAuthStore } from '@/lib/store';

export function useAuth() {
  const { user, isAuthenticated, login, signup, logout, loadUser } = useAuthStore();

  return {
    user,
    isAuthenticated,
    login,
    signup,
    logout,
    signOut: logout, // Alias for logout
    loadUser,
    loading: false, // Can be enhanced with loading state
    isLoading: false,
  };
}
