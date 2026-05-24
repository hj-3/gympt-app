'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useWorkoutStore } from '@/lib/store';
import { usePostureAnalysis } from '@/hooks/usePostureAnalysis';
import { VideoFeed } from '@/components/workout/VideoFeed';
import { PostureFeedback } from '@/components/workout/PostureFeedback';
import { RepCounter } from '@/components/workout/RepCounter';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import toast from 'react-hot-toast';

export default function WorkoutPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { currentSession, startSession, completeSession } = useWorkoutStore();
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [exercise, setExercise] = useState('squat');
  const [sessionId, setSessionId] = useState<string | null>(null);

  const {
    connect,
    disconnect,
    sendFrame,
    analysis,
    repCount,
    isConnected,
  } = usePostureAnalysis();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const handleStartSession = async () => {
    if (!user) return;

    try {
      // Start workout session in backend
      await startSession(user.userId, 'default-routine');

      // Generate session ID
      const sid = `session-${Date.now()}`;
      setSessionId(sid);

      // Connect to posture analysis WebSocket
      await connect(sid);

      setIsSessionActive(true);
      toast.success('운동 세션이 시작되었습니다!');
    } catch (error) {
      console.error('Failed to start session:', error);
      toast.error('세션 시작에 실패했습니다');
    }
  };

  const handleEndSession = async () => {
    try {
      disconnect();

      if (currentSession) {
        await completeSession();
      }

      setIsSessionActive(false);
      setSessionId(null);
      toast.success('운동 세션이 종료되었습니다!');

      // Redirect to dashboard after short delay
      setTimeout(() => {
        router.push('/dashboard');
      }, 1500);
    } catch (error) {
      console.error('Failed to end session:', error);
      toast.error('세션 종료에 실패했습니다');
    }
  };

  const handleFrameCapture = (frame: string) => {
    if (isConnected) {
      sendFrame(frame, exercise);
    }
  };

  const exercises = [
    { value: 'squat', label: '스쿼트' },
    { value: 'pushup', label: '푸시업' },
    { value: 'lunge', label: '런지' },
    { value: 'plank', label: '플랭크' },
  ];

  if (!user) return null;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">운동 세션</h1>
        <p className="text-gray-600">
          실시간 자세 분석으로 정확한 운동을 시작하세요
        </p>
      </div>

      {!isSessionActive ? (
        <Card className="max-w-2xl mx-auto text-center py-12">
          <h2 className="text-2xl font-semibold mb-4">운동 준비</h2>
          <p className="text-gray-600 mb-6">
            운동을 선택하고 시작 버튼을 눌러주세요
          </p>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              운동 선택
            </label>
            <select
              value={exercise}
              onChange={(e) => setExercise(e.target.value)}
              className="w-full max-w-xs mx-auto px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {exercises.map((ex) => (
                <option key={ex.value} value={ex.value}>
                  {ex.label}
                </option>
              ))}
            </select>
          </div>

          <Button onClick={handleStartSession} size="lg">
            운동 시작
          </Button>
        </Card>
      ) : (
        <div className="grid md:grid-cols-3 gap-8">
          <div className="md:col-span-2 space-y-4">
            <VideoFeed
              isActive={isSessionActive}
              onFrame={handleFrameCapture}
              exercise={exercise}
            />

            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  운동 변경
                </label>
                <select
                  value={exercise}
                  onChange={(e) => setExercise(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {exercises.map((ex) => (
                    <option key={ex.value} value={ex.value}>
                      {ex.label}
                    </option>
                  ))}
                </select>
              </div>

              <Button
                onClick={handleEndSession}
                variant="danger"
                size="lg"
              >
                운동 종료
              </Button>
            </div>
          </div>

          <div className="space-y-6">
            <RepCounter count={repCount} exercise={exercise} />
            <PostureFeedback analysis={analysis} />

            <Card>
              <h3 className="font-semibold mb-2">연결 상태</h3>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {isConnected ? '연결됨' : '연결 끊김'}
                </span>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
