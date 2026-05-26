import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { ApiResponse } from '@/types';
import { getAuthToken } from './auth';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - add Cognito token
    this.client.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        const token = await getAuthToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired, redirect to login
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Body Profile API
  async createBodyProfile(data: any): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/v1/body-profiles', data);
    return response.data;
  }

  async getLatestBodyProfile(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/api/v1/body-profiles/latest');
    return response.data;
  }

  async getBodyProfileHistory(limit?: number): Promise<ApiResponse<any>> {
    const params = limit ? { limit } : {};
    const response = await this.client.get('/api/v1/body-profiles/history', { params });
    return response.data;
  }

  // Workout Goal API
  async createGoal(data: any): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/v1/goals', data);
    return response.data;
  }

  async getLatestGoal(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/api/v1/goals/latest');
    return response.data;
  }

  async getGoalHistory(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/api/v1/goals/history');
    return response.data;
  }

  // Workout Routine API
  async getTodayRoutine(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/v1/routines/today/${userId}`);
    return response.data;
  }

  async getRoutines(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/v1/routines/${userId}`);
    return response.data;
  }

  // Workout Session API
  async startSession(userId: string, routineId: string): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/v1/sessions/start', {
      userId,
      routineId,
    });
    return response.data;
  }

  async completeSession(sessionId: string): Promise<ApiResponse<any>> {
    const response = await this.client.post(`/api/v1/sessions/${sessionId}/complete`);
    return response.data;
  }

  async getSession(sessionId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/v1/sessions/${sessionId}`);
    return response.data;
  }

  // Workout Report API
  async getReport(sessionId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/v1/reports/${sessionId}`);
    return response.data;
  }

  async getReports(userId: string, page = 1, limit = 10): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/v1/reports/user/${userId}`, {
      params: { page, limit },
    });
    return response.data;
  }

  // Dashboard API
  async getStats(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/v1/stats/${userId}`);
    return response.data;
  }

  async getWeeklyProgress(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/v1/stats/${userId}/weekly`);
    return response.data;
  }

  // KVS Credentials API
  async getKVSCredentials(sessionId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/v1/kvs/credentials/${sessionId}`);
    return response.data;
  }

  // AI Agent API (via backend-api gateway)
  async getWorkoutRecommendation(data: {
    user_id: string;
    goal: string;
    fitness_level: string;
    days_per_week: number;
    equipment_available?: string[];
    injuries_or_limitations?: string;
    height?: number;
    weight?: number;
    body_fat?: number;
    muscle_mass?: number;
  }): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/v1/agent/workout-recommendation', data, {
      timeout: 60000, // AI 응답은 시간이 걸릴 수 있음
    });
    return response.data;
  }

  async getPostureFeedback(data: {
    user_id: string;
    session_id: string;
    exercise_name: string;
    posture_issues?: string[];
  }): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/v1/agent/posture-feedback', data, {
      timeout: 60000,
    });
    return response.data;
  }

  // User API
  async getCurrentUserProfile(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/api/v1/users/me');
    return response.data;
  }

  async updateCurrentUserProfile(data: any): Promise<ApiResponse<any>> {
    const response = await this.client.put('/api/v1/users/me', data);
    return response.data;
  }

  async deleteCurrentAccount(): Promise<ApiResponse<void>> {
    const response = await this.client.delete('/api/v1/users/me');
    return response.data;
  }
}

export const apiClient = new ApiClient();
