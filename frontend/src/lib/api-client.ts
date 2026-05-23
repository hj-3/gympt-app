import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { AuthResponse, ApiResponse } from '@/types';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.loadTokensFromStorage();
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (this.accessToken && config.headers) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${token}`;
                }
                resolve(this.client(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            const newAccessToken = await this.refreshAccessToken();
            this.isRefreshing = false;
            this.onRefreshed(newAccessToken);
            this.refreshSubscribers = [];

            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            this.isRefreshing = false;
            this.clearTokens();
            if (typeof window !== 'undefined') {
              window.location.href = '/login';
            }
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private onRefreshed(token: string) {
    this.refreshSubscribers.forEach((callback) => callback(token));
  }

  private async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await axios.post<AuthResponse>(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/refresh`,
      { refreshToken: this.refreshToken }
    );

    this.setTokens(response.data.accessToken, response.data.refreshToken);
    return response.data.accessToken;
  }

  private loadTokensFromStorage() {
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('accessToken');
      this.refreshToken = localStorage.getItem('refreshToken');
    }
  }

  public setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;

    if (typeof window !== 'undefined') {
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
    }
  }

  public clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;

    if (typeof window !== 'undefined') {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }

  public getAccessToken(): string | null {
    return this.accessToken;
  }

  public isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  // Auth API
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/api/v1/auth/login', {
      email,
      password,
    });
    this.setTokens(response.data.accessToken, response.data.refreshToken);
    return response.data;
  }

  async signup(email: string, password: string, name: string): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/api/v1/auth/register', {
      email,
      password,
      name,
    });
    this.setTokens(response.data.accessToken, response.data.refreshToken);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await this.client.post('/api/v1/auth/logout');
    } finally {
      this.clearTokens();
    }
  }

  async getCurrentUser(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/api/users/me');
    return response.data;
  }

  // Body Profile API
  async getBodyProfile(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/body-profile/${userId}`);
    return response.data;
  }

  async updateBodyProfile(userId: string, data: any): Promise<ApiResponse<any>> {
    const response = await this.client.put(`/api/body-profile/${userId}`, data);
    return response.data;
  }

  // Workout Goal API
  async getWorkoutGoal(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/workout-goals/${userId}`);
    return response.data;
  }

  async updateWorkoutGoal(userId: string, data: any): Promise<ApiResponse<any>> {
    const response = await this.client.put(`/api/workout-goals/${userId}`, data);
    return response.data;
  }

  // Workout Routine API
  async getTodayRoutine(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/routines/today/${userId}`);
    return response.data;
  }

  async getRoutines(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/routines/${userId}`);
    return response.data;
  }

  // Workout Session API
  async startSession(userId: string, routineId: string): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/sessions/start', {
      userId,
      routineId,
    });
    return response.data;
  }

  async completeSession(sessionId: string): Promise<ApiResponse<any>> {
    const response = await this.client.post(`/api/sessions/${sessionId}/complete`);
    return response.data;
  }

  async getSession(sessionId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/sessions/${sessionId}`);
    return response.data;
  }

  // Workout Report API
  async getReport(sessionId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/reports/${sessionId}`);
    return response.data;
  }

  async getReports(userId: string, page = 1, limit = 10): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/reports/user/${userId}`, {
      params: { page, limit },
    });
    return response.data;
  }

  // Dashboard API
  async getStats(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/stats/${userId}`);
    return response.data;
  }

  async getWeeklyProgress(userId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/stats/${userId}/weekly`);
    return response.data;
  }

  // KVS Credentials API
  async getKVSCredentials(sessionId: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/kvs/credentials/${sessionId}`);
    return response.data;
  }
}

export const apiClient = new ApiClient();
