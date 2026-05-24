'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api-client';
import {
  VideoCameraIcon,
  PlayIcon,
  StopIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

type SessionState = 'idle' | 'requesting_permission' | 'ready' | 'active' | 'completed' | 'error';

export default function SessionPage() {
  const router = useRouter();
  const { user } = useAuth();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [sessionState, setSessionState] = useState<SessionState>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<number>(0);

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
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

  const startWorkoutSession = async () => {
    if (!user?.userId) {
      toast.error('사용자 정보를 찾을 수 없습니다');
      return;
    }

    try {
      const routineResponse = await apiClient.getTodayRoutine(user.userId);
      const routine = routineResponse.data;

      if (!routine) {
        toast.error('오늘의 운동 루틴이 없습니다');
        return;
      }

      const sessionResponse = await apiClient.startSession(user.userId, routine.routineId);
      const session = sessionResponse.data;

      setSessionId(session.sessionId);
      setSessionState('active');
      toast.success('운동을 시작합니다!');

    } catch (error: any) {
      console.error('Failed to start session:', error);
      if (error.response?.status === 404) {
        toast.error('운동 루틴이 설정되지 않았습니다');
      } else {
        toast.error('세션 시작에 실패했습니다');
      }
    }
  };

  const stopWorkoutSession = async () => {
    if (!sessionId) return;

    try {
      await apiClient.completeSession(sessionId);
      setSessionState('completed');
      toast.success('운동이 완료되었습니다!');

      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        setStream(null);
      }

      setTimeout(() => {
        router.push(`/report/${sessionId}`);
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
        <div className="max-w-4xl mx-auto">
          <div className="relative aspect-video bg-black">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/60 to-transparent">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {sessionState === 'active' && (
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                        <span className="text-white text-sm font-medium">운동 중</span>
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
          <div className="bg-gray-800 p-6">
            <div className="flex items-center justify-center gap-4">
              {sessionState === 'idle' && (
                <button onClick={requestCameraPermission} className="px-8 py-4 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 transition-colors flex items-center gap-3">
                  <VideoCameraIcon className="w-6 h-6" />
                  <span className="font-semibold">카메라 시작</span>
                </button>
              )}
              {sessionState === 'ready' && (
                <button onClick={startCountdown} className="px-8 py-4 bg-green-600 text-white rounded-2xl hover:bg-green-700 transition-colors flex items-center gap-3">
                  <PlayIcon className="w-6 h-6" />
                  <span className="font-semibold">운동 시작</span>
                </button>
              )}
              {sessionState === 'active' && (
                <button onClick={stopWorkoutSession} className="px-8 py-4 bg-red-600 text-white rounded-2xl hover:bg-red-700 transition-colors flex items-center gap-3">
                  <StopIcon className="w-6 h-6" />
                  <span className="font-semibold">운동 종료</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
