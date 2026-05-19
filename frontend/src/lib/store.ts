import { create } from 'zustand';
import { User, WorkoutSession, RealtimeFeedback } from '@/types';
import { apiClient } from './api-client';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, name: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
}

interface WorkoutState {
  currentSession: WorkoutSession | null;
  realtimeFeedback: RealtimeFeedback[];
  startSession: (userId: string, routineId: string) => Promise<void>;
  completeSession: () => Promise<void>;
  addFeedback: (feedback: RealtimeFeedback) => void;
  clearFeedback: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,

  login: async (email, password) => {
    const response = await apiClient.login(email, password);
    set({ user: response.user, isAuthenticated: true });
  },

  signup: async (email, password, name) => {
    const response = await apiClient.signup(email, password, name);
    set({ user: response.user, isAuthenticated: true });
  },

  logout: async () => {
    await apiClient.logout();
    set({ user: null, isAuthenticated: false });
  },

  loadUser: async () => {
    if (apiClient.isAuthenticated()) {
      try {
        const response = await apiClient.getCurrentUser();
        set({ user: response.data, isAuthenticated: true });
      } catch (error) {
        set({ user: null, isAuthenticated: false });
      }
    }
  },
}));

export const useWorkoutStore = create<WorkoutState>((set, get) => ({
  currentSession: null,
  realtimeFeedback: [],

  startSession: async (userId, routineId) => {
    const response = await apiClient.startSession(userId, routineId);
    set({ currentSession: response.data, realtimeFeedback: [] });
  },

  completeSession: async () => {
    const session = get().currentSession;
    if (session) {
      await apiClient.completeSession(session.sessionId);
      set({ currentSession: null, realtimeFeedback: [] });
    }
  },

  addFeedback: (feedback) => {
    set((state) => ({
      realtimeFeedback: [...state.realtimeFeedback, feedback].slice(-50), // Keep last 50
    }));
  },

  clearFeedback: () => {
    set({ realtimeFeedback: [] });
  },
}));
