'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api-client';
import { postureApi, AnalyzeFrameResponse } from '@/lib/posture-api';
import { PoseCanvas, Landmark } from '@/components/workout/PoseCanvas';
import { FeedbackPanel, FeedbackData } from '@/components/workout/FeedbackPanel';
import {
  VideoCameraIcon,
  PlayIcon,
  StopIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

type SessionState = 'idle' | 'requesting_permission' | 'ready' | 'active' | 'completed' | 'error';

export default function SessionPage() {
  const router = useRouter();
  const { user } = useAuth();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const analysisIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [sessionState, setSessionState] = useState<SessionState>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<number>(0);
  const [currentExercise, setCurrentExercise] = useState<string>('squat');
  const [repCount, setRepCount] = useState<number>(0);
  const [feedback, setFeedback] = useState<FeedbackData | null>(null);
  const [landmarks] = useState<Landmark[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      if (analysisIntervalRef.current) {
        clearInterval(analysisIntervalRef.current);
      }
    };
  }, [stream]);

  const requestCameraPermission = async () => {
    setSessionState('requesting_permission');
    setError(null);

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
        audio: false,
      });

      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }

      setSessionState('ready');
      toast.success('카메라 연결 완료');
    } catch (err: any) {
      console.error('Camera permission error:', err);
      let errorMessage = '카메라 권한을 허용해주세요';

      if (err.name === 'NotAllowedError') {
        errorMessage = '카메라 접근이 거부되었습니다. 브라우저 설정에서 권한을 허용해주세요';
      } else if (err.name === 'NotFoundError') {
        errorMessage = '카메라를 찾을 수 없습니다';
      } else if (err.name === 'NotReadableError') {
        errorMessage = '카메라가 다른 앱에서 사용 중입니다';
      }

      setError(errorMessage);
      setSessionState('error');
      toast.error(errorMessage);
    }
  };

  const captureFrame = (): string | null => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) return null;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL('image/jpeg', 0.8);
  };

  const analyzeFrame = async () => {
    if (!sessionId || !user?.userId || isAnalyzing) return;

    const frameBase64 = captureFrame();
    if (!frameBase64) return;

    setIsAnalyzing(true);

    try {
      const response: AnalyzeFrameResponse = await postureApi.analyzeFrame({
        exercise: currentExercise,
        frame_base64: frameBase64,
        session_id: sessionId,
        user_id: user.userId,
        rep_count: repCount,
        send_websocket: false,
      });

      setFeedback({
        form_score: response.form_score,
        is_valid: response.is_valid,
        feedback: response.feedback,
        rep_count: repCount,
      });

    } catch (error) {
      console.error('Frame analysis error:', error);
      // Don't show error to user for every failed frame
    } finally {
      setIsAnalyzing(false);
    }
  };

  const startWorkoutSession = async () => {
    if (!user?.userId) {
      toast.error('사용자 정보를 찾을 수 없습니다');
      return;
    }

    try {
      // 루틴이 없어도 자유 운동 모드로 세션 시작 가능
      let routineId: string | null = null;
      try {
        const routineResponse = await apiClient.getTodayRoutine(user.userId);
        routineId = routineResponse.data?.routineId ?? null;
      } catch {
        // 루틴 없음 - 자유 운동으로 진행
      }

      const sessionResponse = await apiClient.startSession(user.userId, routineId ?? 'free-workout');
      const session = sessionResponse.data;

      setSessionId(session.sessionId);
      setSessionState('active');
      toast.success('운동을 시작합니다!');

      // Start periodic frame analysis (every 2 seconds)
      analysisIntervalRef.current = setInterval(() => {
        analyzeFrame();
      }, 2000);

    } catch (error: any) {
      console.error('Failed to start session:', error);
      toast.error('세션 시작에 실패했습니다');
      setSessionState('ready');
    }
  };

  const stopWorkoutSession = async () => {
    if (!sessionId) return;

    if (analysisIntervalRef.current) {
      clearInterval(analysisIntervalRef.current);
      analysisIntervalRef.current = null;
    }

    try {
      await apiClient.completeSession(sessionId);
      setSessionState('completed');
      toast.success('운동이 완료되었습니다!');

      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        setStream(null);
      }

      setTimeout(() => {
        router.push(`/report/detail?sessionId=${sessionId}`);
      }, 1500);
    } catch (error) {
      console.error('Failed to complete session:', error);
      toast.error('세션 종료에 실패했습니다');
    }
  };

  const startCountdown = () => {
    setCountdown(3);
    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          startWorkoutSession();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
            {/* Video and Pose Overlay */}
            <div className="lg:col-span-2">
              <div className="relative aspect-video bg-black rounded-2xl overflow-hidden">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
                {/* Hidden canvas for frame capture */}
                <canvas ref={canvasRef} className="hidden" />

                {/* Pose overlay */}
                {sessionState === 'active' && landmarks.length > 0 && (
                  <div className="absolute inset-0 pointer-events-none">
                    <PoseCanvas
                      landmarks={landmarks}
                      width={videoRef.current?.videoWidth || 1280}
                      height={videoRef.current?.videoHeight || 720}
                      className="w-full h-full"
                    />
                  </div>
                )}

                <div className="absolute inset-0 pointer-events-none">
                  <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/60 to-transparent">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {sessionState === 'active' && (
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                            <span className="text-white text-sm font-medium">운동 중</span>
                            {isAnalyzing && (
                              <span className="text-blue-400 text-xs">분석 중...</span>
                            )}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => router.back()}
                        className="text-white px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors pointer-events-auto"
                      >
                        닫기
                      </button>
                    </div>
                  </div>
                  {countdown > 0 && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-white text-9xl font-bold animate-pulse">
                        {countdown}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Controls */}
              <div className="mt-4 bg-gray-800 rounded-2xl p-6">
                <div className="flex items-center justify-center gap-4">
                  {(sessionState === 'idle' || sessionState === 'error') && (
                    <div className="flex flex-col items-center gap-3">
                      <button
                        onClick={requestCameraPermission}
                        className="px-8 py-4 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 transition-colors flex items-center gap-3"
                      >
                        <VideoCameraIcon className="w-6 h-6" />
                        <span className="font-semibold">카메라 시작</span>
                      </button>
                      {error && (
                        <p className="text-red-400 text-sm text-center">{error}</p>
                      )}
                    </div>
                  )}
                  {sessionState === 'ready' && (
                    <button
                      onClick={startCountdown}
                      className="px-8 py-4 bg-green-600 text-white rounded-2xl hover:bg-green-700 transition-colors flex items-center gap-3"
                    >
                      <PlayIcon className="w-6 h-6" />
                      <span className="font-semibold">운동 시작</span>
                    </button>
                  )}
                  {sessionState === 'active' && (
                    <button
                      onClick={stopWorkoutSession}
                      className="px-8 py-4 bg-red-600 text-white rounded-2xl hover:bg-red-700 transition-colors flex items-center gap-3"
                    >
                      <StopIcon className="w-6 h-6" />
                      <span className="font-semibold">운동 종료</span>
                    </button>
                  )}
                </div>

                {/* Exercise Selector */}
                {sessionState === 'ready' && (
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <label className="block text-white text-sm font-medium mb-2">
                      운동 선택
                    </label>
                    <select
                      value={currentExercise}
                      onChange={(e) => setCurrentExercise(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="squat">스쿼트</option>
                      <option value="pushup">푸시업</option>
                      <option value="plank">플랭크</option>
                      <option value="lunge">런지</option>
                    </select>
                  </div>
                )}
              </div>
            </div>

            {/* Feedback Panel */}
            <div className="lg:col-span-1">
              <FeedbackPanel feedback={feedback} className="h-full" />

              {/* Exercise Info */}
              {sessionState === 'active' && (
                <div className="mt-4 bg-gray-800 rounded-2xl p-6">
                  <h3 className="text-white font-semibold mb-3">현재 운동</h3>
                  <p className="text-2xl font-bold text-blue-400 capitalize">
                    {currentExercise}
                  </p>
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 text-sm">목표 횟수</span>
                      <span className="text-white font-semibold">12회</span>
                    </div>
                    <div className="flex justify-between items-center mt-2">
                      <span className="text-gray-400 text-sm">현재 세트</span>
                      <span className="text-white font-semibold">1/3</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
