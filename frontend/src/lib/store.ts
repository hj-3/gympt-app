import { create } from 'zustand';
import { WorkoutSession, RealtimeFeedback } from '@/types';
import { apiClient } from './api-client';
import {
  loginWithCognito,
  signupWithCognito,
  logoutFromCognito,
  getCurrentCognitoUser,
  isAuthenticated as checkAuth,
  CognitoUser,
} from './auth';

interface AuthState {
  user: CognitoUser | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  signup: (username: string, email: string, password: string, name: string, phoneNumber?: string) => Promise<void>;
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

  login: async (username, password) => {
    const user = await loginWithCognito(username, password);
    set({ user, isAuthenticated: true });
  },

  signup: async (username, email, password, name, phoneNumber) => {
    await signupWithCognito(username, email, password, name, phoneNumber);
    // After signup, user needs to verify email, then login
    set({ user: null, isAuthenticated: false });
  },

  logout: async () => {
    await logoutFromCognito();
    set({ user: null, isAuthenticated: false });
  },

  loadUser: async () => {
    try {
      const authenticated = await checkAuth();
      if (authenticated) {
        const user = await getCurrentCognitoUser();
        set({ user, isAuthenticated: true });
      } else {
        set({ user: null, isAuthenticated: false });
      }
    } catch (error) {
      set({ user: null, isAuthenticated: false });
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
