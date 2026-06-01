/**
 * Posture Analysis API Client
 */
import axios from 'axios';

// 브라우저 → backend-api → posture-analysis-service (클러스터 내부)
// 정적 배포(S3+CloudFront)라 Next.js API 라우트 불가 → backend-api 프록시 사용
const postureApiClient = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/api/v1/posture`,
  timeout: 10000,
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
