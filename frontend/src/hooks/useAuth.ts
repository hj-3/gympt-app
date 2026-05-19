import { useAuthStore } from '@/lib/store';

export function useAuth() {
  const { user, isAuthenticated, login, signup, logout, loadUser } = useAuthStore();

  return {
    user,
    isAuthenticated,
    login,
    signup,
    logout,
    loadUser,
    isLoading: false, // Can be enhanced with loading state
  };
}
