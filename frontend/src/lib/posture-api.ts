/**
 * Posture Analysis API Client
 */
import axios from 'axios';

const postureApiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_POSTURE_API_URL || 'http://localhost:8002/api/v1',
  timeout: 5000,
});

export interface AnalyzeFrameRequest {
  exercise: string;
  frame_base64: string;
  rep_phase?: string;
  session_id?: string;
  user_id?: string;
  rep_count?: number;
  send_websocket?: boolean;
}

export interface AnalyzeFrameResponse {
  form_score: number;
  is_valid: boolean;
  feedback: string[];
  angles: Record<string, number>;
  landmarks_count: number;
}

export const postureApi = {
  /**
   * Analyze a single frame
   */
  analyzeFrame: async (request: AnalyzeFrameRequest): Promise<AnalyzeFrameResponse> => {
    // Remove data URL prefix if present
    let base64 = request.frame_base64;
    if (base64.startsWith('data:image')) {
      base64 = base64.split(',')[1];
    }

    const response = await postureApiClient.post<AnalyzeFrameResponse>('/analyze', {
      ...request,
      frame_base64: base64,
    });

    return response.data;
  },

  /**
   * Get supported exercises
   */
  getExercises: async () => {
    const response = await postureApiClient.get('/exercises');
    return response.data.exercises;
  },
};

export default postureApi;
