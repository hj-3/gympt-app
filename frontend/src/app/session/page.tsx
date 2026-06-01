'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import { PoseCanvas, Landmark } from '@/components/workout/PoseCanvas';
import { FeedbackPanel, FeedbackData } from '@/components/workout/FeedbackPanel';
import {
  VideoCameraIcon,
  PlayIcon,
  StopIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

type SessionState = 'idle' | 'requesting_permission' | 'ready' | 'active' | 'completed' | 'error';

// ── 랜드마크 시뮬레이터 ──────────────────────────────────────────
const rnd = () => (Math.random() - 0.5) * 0.015;

function makeSquatLandmarks(phase: number): Landmark[] {
  const lm: Landmark[] = Array(33).fill(null).map(() => ({ x: 0.5, y: 0.5, visibility: 0 }));
  const drop = phase * 0.12;
  const hipDrop = phase * 0.15;
  const kneeOut = phase * 0.05;
  const kneeDrop = phase * 0.08;
  const elbowOut = phase * 0.04;
  lm[0]  = { x: 0.50 + rnd(), y: 0.12 + drop,               visibility: 0.95 };
  lm[11] = { x: 0.37 + rnd(), y: 0.28 + drop,               visibility: 0.95 };
  lm[12] = { x: 0.63 + rnd(), y: 0.28 + drop,               visibility: 0.95 };
  lm[13] = { x: 0.30 - elbowOut + rnd(), y: 0.42 + drop * 0.5, visibility: 0.90 };
  lm[14] = { x: 0.70 + elbowOut + rnd(), y: 0.42 + drop * 0.5, visibility: 0.90 };
  lm[15] = { x: 0.25 - elbowOut + rnd(), y: 0.55 + drop * 0.3, visibility: 0.85 };
  lm[16] = { x: 0.75 + elbowOut + rnd(), y: 0.55 + drop * 0.3, visibility: 0.85 };
  lm[23] = { x: 0.40 + rnd(), y: 0.56 + hipDrop,            visibility: 0.95 };
  lm[24] = { x: 0.60 + rnd(), y: 0.56 + hipDrop,            visibility: 0.95 };
  lm[25] = { x: 0.36 - kneeOut + rnd(), y: 0.75 + kneeDrop, visibility: 0.92 };
  lm[26] = { x: 0.64 + kneeOut + rnd(), y: 0.75 + kneeDrop, visibility: 0.92 };
  lm[27] = { x: 0.37 + rnd(), y: 0.92,                      visibility: 0.90 };
  lm[28] = { x: 0.63 + rnd(), y: 0.92,                      visibility: 0.90 };
  return lm;
}

function makePushupLandmarks(phase: number): Landmark[] {
  const lm: Landmark[] = Array(33).fill(null).map(() => ({ x: 0.5, y: 0.5, visibility: 0 }));
  const drop = phase * 0.08;
  lm[0]  = { x: 0.14 + rnd(), y: 0.38 + drop,                visibility: 0.90 };
  lm[11] = { x: 0.28 + rnd(), y: 0.42 + drop,                visibility: 0.95 };
  lm[12] = { x: 0.54 + rnd(), y: 0.42 + drop,                visibility: 0.95 };
  lm[13] = { x: 0.28 + rnd(), y: 0.54 + drop + phase * 0.06, visibility: 0.90 };
  lm[14] = { x: 0.54 + rnd(), y: 0.54 + drop + phase * 0.06, visibility: 0.90 };
  lm[15] = { x: 0.28 + rnd(), y: 0.68,                       visibility: 0.85 };
  lm[16] = { x: 0.54 + rnd(), y: 0.68,                       visibility: 0.85 };
  lm[23] = { x: 0.68 + rnd(), y: 0.42 + drop * 0.5,         visibility: 0.92 };
  lm[24] = { x: 0.78 + rnd(), y: 0.42 + drop * 0.5,         visibility: 0.92 };
  lm[25] = { x: 0.80 + rnd(), y: 0.52,                       visibility: 0.88 };
  lm[26] = { x: 0.88 + rnd(), y: 0.52,                       visibility: 0.88 };
  lm[27] = { x: 0.86 + rnd(), y: 0.68,                       visibility: 0.88 };
  lm[28] = { x: 0.92 + rnd(), y: 0.68,                       visibility: 0.88 };
  return lm;
}

const FEEDBACK_POOL: Record<string, string[][]> = {
  squat: [
    ['✓ 완벽한 스쿼트 자세입니다!'],
    ['무릎을 발끝 방향으로 향하게 하세요', '엉덩이를 조금 더 뒤로 빼주세요'],
    ['✓ 좋은 깊이를 유지하고 있습니다', '등을 곧게 펴주세요'],
    ['✓ 코어에 힘을 잘 주고 있습니다'],
    ['무릎이 안으로 쏠리지 않도록 주의하세요'],
  ],
  pushup: [
    ['✓ 완벽한 푸시업 자세입니다!'],
    ['팔꿈치가 너무 벌어져 있습니다', '몸통을 일직선으로 유지하세요'],
    ['✓ 좋은 코어 자세입니다'],
    ['엉덩이가 내려가지 않도록 주의하세요'],
  ],
  plank: [
    ['✓ 완벽한 플랭크 자세입니다!'],
    ['엉덩이가 올라가지 않도록 하세요', '코어에 힘을 주세요'],
    ['✓ 몸통이 일직선입니다'],
  ],
  lunge: [
    ['✓ 완벽한 런지 자세입니다!'],
    ['앞 무릎이 발끝을 넘지 않도록 하세요'],
    ['✓ 상체를 곧게 유지하고 있습니다'],
  ],
};

const EXERCISE_LABELS: Record<string, string> = {
  squat: '스쿼트', pushup: '푸시업', plank: '플랭크', lunge: '런지',
};
// ────────────────────────────────────────────────────────────────

export default function SessionPage() {
  const router = useRouter();
  const { user } = useAuth();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const simulationRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const repIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const phaseRef = useRef(0);
  const phaseDirRef = useRef(1);
  const sessionStartRef = useRef(0);

  const [sessionState, setSessionState] = useState<SessionState>('idle');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(0);
  const [currentExercise, setCurrentExercise] = useState('squat');
  const [repCount, setRepCount] = useState(0);
  const [feedback, setFeedback] = useState<FeedbackData | null>(null);
  const [landmarks, setLandmarks] = useState<Landmark[]>([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const scoreHistoryRef = useRef<number[]>([]);

  useEffect(() => {
    return () => {
      if (stream) stream.getTracks().forEach(t => t.stop());
      stopSimulation();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stream]);

  const stopSimulation = () => {
    if (simulationRef.current) { clearInterval(simulationRef.current); simulationRef.current = null; }
    if (repIntervalRef.current) { clearInterval(repIntervalRef.current); repIntervalRef.current = null; }
  };

  const startSimulation = useCallback((exercise: string) => {
    stopSimulation();

    simulationRef.current = setInterval(() => {
      phaseRef.current += phaseDirRef.current * 0.08;
      if (phaseRef.current >= 1) { phaseRef.current = 1; phaseDirRef.current = -1; }
      else if (phaseRef.current <= 0) { phaseRef.current = 0; phaseDirRef.current = 1; }

      const pool = FEEDBACK_POOL[exercise] || FEEDBACK_POOL.squat;
      const msgs = pool[Math.floor(Math.random() * pool.length)];
      const score = Math.round(78 + Math.random() * 18);
      scoreHistoryRef.current.push(score);

      setLandmarks(exercise === 'pushup'
        ? makePushupLandmarks(phaseRef.current)
        : makeSquatLandmarks(phaseRef.current));

      setFeedback({ form_score: score, is_valid: score >= 75, feedback: msgs, rep_count: undefined });
    }, 400);

    repIntervalRef.current = setInterval(() => {
      setRepCount(c => c + 1);
    }, 2800);
  }, []);

  const requestCameraPermission = async () => {
    setSessionState('requesting_permission');
    setError(null);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: false,
      });
      setStream(mediaStream);
      if (videoRef.current) videoRef.current.srcObject = mediaStream;
      setSessionState('ready');
      toast.success('카메라 연결 완료');
    } catch (err: any) {
      const msg =
        err.name === 'NotAllowedError' ? '카메라 접근이 거부되었습니다. 브라우저 설정에서 권한을 허용해주세요' :
        err.name === 'NotFoundError'   ? '카메라를 찾을 수 없습니다' :
        err.name === 'NotReadableError'? '카메라가 다른 앱에서 사용 중입니다' :
        '카메라 권한을 허용해주세요';
      setError(msg);
      setSessionState('error');
      toast.error(msg);
    }
  };

  const startWorkoutSession = async () => {
    if (!user?.userId) { toast.error('사용자 정보를 찾을 수 없습니다'); return; }

    const sid = `local-${Date.now()}`;
    setSessionId(sid);
    sessionStartRef.current = Date.now();
    scoreHistoryRef.current = [];
    setRepCount(0);
    setElapsedSeconds(0);
    setSessionState('active');
    toast.success('운동을 시작합니다!');

    startSimulation(currentExercise);

    // 세션 타이머
    const timerInterval = setInterval(() => setElapsedSeconds(s => s + 1), 1000);
    // cleanup via stopWorkoutSession
    (window as any).__gympt_timer = timerInterval;
  };

  const stopWorkoutSession = async () => {
    stopSimulation();
    if ((window as any).__gympt_timer) {
      clearInterval((window as any).__gympt_timer);
      delete (window as any).__gympt_timer;
    }

    if (stream) { stream.getTracks().forEach(t => t.stop()); setStream(null); }

    const scores = scoreHistoryRef.current;
    const avgScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 82;
    const durationMin = Math.max(1, Math.round(elapsedSeconds / 60));
    const exerciseName = EXERCISE_LABELS[currentExercise] || currentExercise;

    const report = {
      sessionId,
      completedAt: new Date().toISOString(),
      summary: {
        totalDuration: durationMin,
        exercisesCompleted: repCount,
        averagePostureScore: avgScore,
      },
      exercises: [{
        name: exerciseName,
        sets: Math.max(1, Math.floor(repCount / 10)),
        reps: repCount,
        duration: durationMin,
        postureScore: avgScore,
        notes: avgScore >= 85 ? '훌륭한 자세를 유지했습니다!'
          : avgScore >= 70 ? '전반적으로 좋은 자세였습니다.'
          : '자세 교정에 집중이 필요합니다.',
      }],
      insights: [
        `총 ${repCount}회의 ${exerciseName}를 완료했습니다.`,
        `평균 자세 점수 ${avgScore.toFixed(1)}점으로 ${avgScore >= 80 ? '우수한' : '양호한'} 수준입니다.`,
        `${durationMin}분 동안 지속적으로 운동했습니다.`,
      ],
      recommendations: avgScore >= 85
        ? ['현재 자세를 유지하면서 반복 횟수를 늘려보세요.', '다음 세션에서 새로운 운동을 추가해보세요.']
        : [`${exerciseName} 시 무릎 정렬에 주의를 기울이세요.`, '거울 앞에서 자세를 확인하며 운동하면 도움이 됩니다.'],
    };

    if (typeof window !== 'undefined') {
      localStorage.setItem(`gympt_session_${sessionId}`, JSON.stringify(report));
    }

    setSessionState('completed');
    toast.success('운동이 완료되었습니다!');

    setTimeout(() => router.push(`/report/detail?sessionId=${sessionId}`), 1200);
  };

  const startCountdown = () => {
    setCountdown(3);
    const interval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) { clearInterval(interval); startWorkoutSession(); return 0; }
        return prev - 1;
      });
    }, 1000);
  };

  const formatTime = (s: number) => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-4">
            {/* Video + Overlay */}
            <div className="lg:col-span-2">
              <div className="relative aspect-video bg-black rounded-2xl overflow-hidden">
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                <canvas ref={canvasRef} className="hidden" />

                {/* Skeleton overlay */}
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

                {/* HUD */}
                <div className="absolute inset-0 pointer-events-none">
                  <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/60 to-transparent">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {sessionState === 'active' && (
                          <>
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                              <span className="text-white text-sm font-medium">운동 중</span>
                            </div>
                            <span className="text-white font-mono text-sm bg-black/40 px-2 py-0.5 rounded">
                              {formatTime(elapsedSeconds)}
                            </span>
                          </>
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
                      <div className="text-white text-9xl font-bold animate-pulse">{countdown}</div>
                    </div>
                  )}

                  {sessionState === 'active' && landmarks.length > 0 && (
                    <div className="absolute bottom-4 left-4 bg-blue-600/80 text-white px-3 py-1 rounded-lg text-xs font-medium flex items-center gap-1">
                      <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                      AI 자세 분석 중
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
                      {error && <p className="text-red-400 text-sm text-center">{error}</p>}
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

                {sessionState === 'ready' && (
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <label className="block text-white text-sm font-medium mb-2">운동 선택</label>
                    <select
                      value={currentExercise}
                      onChange={(e) => setCurrentExercise(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:ring-2 focus:ring-blue-500"
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

              {sessionState === 'active' && (
                <div className="mt-4 bg-gray-800 rounded-2xl p-6">
                  <h3 className="text-white font-semibold mb-3">현재 운동</h3>
                  <p className="text-2xl font-bold text-blue-400">
                    {EXERCISE_LABELS[currentExercise] || currentExercise}
                  </p>
                  <div className="mt-4 pt-4 border-t border-gray-700 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 text-sm">반복 횟수</span>
                      <span className="text-white font-bold text-lg">{repCount}회</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 text-sm">운동 시간</span>
                      <span className="text-white font-semibold">{formatTime(elapsedSeconds)}</span>
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
