'use client';

import { Suspense, useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api-client';
import { usePostureAnalysis } from '@/hooks/usePostureAnalysis';
import { VideoFeed } from '@/components/workout/VideoFeed';
import { PostureFeedback } from '@/components/workout/PostureFeedback';
import { RepCounter } from '@/components/workout/RepCounter';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import toast from 'react-hot-toast';

const EXERCISE_NAMES: Record<string, string> = {
  squat: '스쿼트',
  pushup: '푸시업',
  lunge: '런지',
  plank: '플랭크',
};

function WorkoutContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated } = useAuthStore();
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [exercise, setExercise] = useState('squat');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const scoreHistoryRef = useRef<number[]>([]);

  // AI 추천에서 넘어온 목표 (세트×횟수). 없으면 자유 운동 모드.
  const [targetSets, setTargetSets] = useState<number | null>(null);
  const [targetReps, setTargetReps] = useState<number | null>(null);
  const recommendationIdRef = useRef<string | null>(null);
  const rdsSessionIdRef = useRef<string | null>(null);

  // 추천 링크의 쿼리 파라미터(exercise/sets/reps/recommendationId) 반영
  useEffect(() => {
    const qExercise = searchParams.get('exercise');
    const qSets = searchParams.get('sets');
    const qReps = searchParams.get('reps');
    const qRecId = searchParams.get('recommendationId');

    if (qExercise && EXERCISE_NAMES[qExercise]) setExercise(qExercise);
    if (qSets) setTargetSets(parseInt(qSets, 10) || null);
    if (qReps) setTargetReps(parseInt(qReps, 10) || null);
    if (qRecId) recommendationIdRef.current = qRecId;
  }, [searchParams]);

  const {
    connect,
    disconnect,
    sendFrame,
    analysis,
    landmarks,
    repCount,
    isConnected,
    poseDetected,
  } = usePostureAnalysis();

  useEffect(() => {
    if (!isAuthenticated) router.push('/login');
  }, [isAuthenticated, router]);

  // Accumulate scores for report — only when a real pose is detected
  useEffect(() => {
    if (analysis && isSessionActive && poseDetected) {
      scoreHistoryRef.current.push(analysis.formScore);
    }
  }, [analysis, isSessionActive, poseDetected]);

  // Session timer
  useEffect(() => {
    if (isSessionActive) {
      timerRef.current = setInterval(() => setElapsedSeconds(s => s + 1), 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      setElapsedSeconds(0);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isSessionActive]);

  const handleStartSession = async () => {
    if (!user) return;

    const sid = `local-${Date.now()}`;
    setSessionId(sid);
    scoreHistoryRef.current = [];
    rdsSessionIdRef.current = null;

    try {
      await connect(sid);
    } catch {
      toast.error('자세 분석 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.');
      setSessionId(null);
      return;
    }

    // Create session record in RDS for dashboard history (non-blocking)
    apiClient.startFreeSession().then((res: any) => {
      if (res?.id) rdsSessionIdRef.current = res.id;
    }).catch((e: any) => console.warn('Failed to create backend session:', e));

    setIsSessionActive(true);
    toast.success('운동 세션이 시작되었습니다!');
  };

  const handleEndSession = async () => {
    disconnect();
    setIsSessionActive(false);

    const scores = scoreHistoryRef.current;
    const avgScore = scores.length > 0
      ? scores.reduce((a, b) => a + b, 0) / scores.length
      : 0;
    const durationMin = Math.max(1, Math.round(elapsedSeconds / 60));

    // AI 추천 목표가 있으면 진행도 계산 (KVS가 센 실제 횟수 / 목표 총 횟수)
    const hasTarget = targetSets != null && targetReps != null;
    const targetTotalReps = hasTarget ? targetSets! * targetReps! : null;
    const progressPercent = targetTotalReps
      ? Math.min(100, Math.round((repCount / targetTotalReps) * 100))
      : null;
    const completedSets = targetReps ? Math.floor(repCount / targetReps) : null;

    // Build session report and save to localStorage
    const sessionReport = {
      sessionId,
      completedAt: new Date().toISOString(),
      exercise,
      exerciseName: EXERCISE_NAMES[exercise] || exercise,
      totalReps: repCount,
      durationSeconds: elapsedSeconds,
      avgScore,
      // 추천 목표 및 진행도 (없으면 null)
      recommendationId: recommendationIdRef.current,
      target: hasTarget
        ? { sets: targetSets, reps: targetReps, totalReps: targetTotalReps }
        : null,
      progress: progressPercent != null
        ? { percent: progressPercent, completedSets, completedReps: repCount }
        : null,
      summary: {
        totalDuration: durationMin,
        exercisesCompleted: 1,
        averagePostureScore: avgScore,
      },
      exercises: [
        {
          name: EXERCISE_NAMES[exercise] || exercise,
          sets: hasTarget ? completedSets : Math.max(1, Math.floor(repCount / 10)),
          reps: repCount,
          targetSets: targetSets,
          targetReps: targetReps,
          progressPercent,
          duration: durationMin,
          postureScore: avgScore,
          notes: avgScore >= 85
            ? '훌륭한 자세를 유지했습니다!'
            : avgScore >= 70
            ? '전반적으로 좋은 자세였습니다. 일부 교정이 필요합니다.'
            : '자세 교정에 집중이 필요합니다.',
        },
      ],
      insights: [
        hasTarget
          ? `목표 ${targetSets}세트 × ${targetReps}회(총 ${targetTotalReps}회) 중 ${repCount}회 완료 (달성률 ${progressPercent}%).`
          : `총 ${repCount}회의 ${EXERCISE_NAMES[exercise] || exercise}를 완료했습니다.`,
        `평균 자세 점수 ${avgScore.toFixed(1)}점으로 ${avgScore >= 80 ? '우수한' : '양호한'} 수준입니다.`,
        `${durationMin}분 동안 지속적으로 운동했습니다.`,
      ],
      recommendations: avgScore >= 85
        ? [
          '현재 자세를 유지하면서 무게나 반복 횟수를 늘려보세요.',
          '다음 세션에서 새로운 운동을 추가해보는 것도 좋습니다.',
        ]
        : [
          `${EXERCISE_NAMES[exercise]} 시 무릎 정렬에 주의를 기울이세요.`,
          '거울 앞에서 자세를 확인하며 운동하면 도움이 됩니다.',
          '가벼운 무게로 자세를 먼저 교정한 후 강도를 높이세요.',
        ],
    };

    // Update per-recommendation progress in localStorage
    if (recommendationIdRef.current && typeof window !== 'undefined') {
      const progressKey = `gympt_rec_progress_${recommendationIdRef.current}`;
      try {
        const existing = JSON.parse(localStorage.getItem(progressKey) || '{}');
        const exerciseProgress = existing.exercises || {};
        exerciseProgress[exercise] = {
          done: true,
          completedAt: new Date().toISOString(),
          totalReps: repCount,
          postureScore: Math.round(avgScore * 10) / 10,
          targetReps: targetReps,
          targetSets: targetSets,
        };
        const allExercises = Object.values(exerciseProgress) as any[];
        const allDone = allExercises.length > 0 && allExercises.every((e: any) => e.done);
        localStorage.setItem(progressKey, JSON.stringify({
          recommendationId: recommendationIdRef.current,
          exercises: exerciseProgress,
          startedAt: existing.startedAt || new Date().toISOString(),
          completedAt: allDone ? new Date().toISOString() : null,
        }));
      } catch { /* ignore */ }
    }

    // Use RDS UUID as localStorage key if available (enables deduplication on dashboard)
    const persistKey = rdsSessionIdRef.current || sessionId;
    const persistedReport = { ...sessionReport, sessionId: persistKey };
    if (typeof window !== 'undefined') {
      localStorage.setItem(`gympt_session_${persistKey}`, JSON.stringify(persistedReport));
    }

    // Mark session COMPLETED in RDS so it appears on the dashboard
    if (rdsSessionIdRef.current) {
      apiClient.completeSession(rdsSessionIdRef.current, {
        totalDuration: elapsedSeconds,
        exerciseType: exercise,
        exerciseName: EXERCISE_NAMES[exercise] || exercise,
        totalReps: repCount,
        avgPostureScore: Math.round(avgScore * 100) / 100,
        ...(recommendationIdRef.current ? { recommendationId: recommendationIdRef.current } : {}),
      }).catch((e: any) => console.warn('Failed to complete backend session:', e));
      rdsSessionIdRef.current = null;
    }

    toast.success('운동이 완료되었습니다! 리포트를 생성합니다...');

    setTimeout(() => {
      router.push(`/report/detail?sessionId=${persistKey}`);
    }, 1200);
  };

  const handleFrameCapture = (frame: string) => {
    if (isConnected && sessionId) {
      sendFrame(frame, exercise);
    }
  };

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
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
        <p className="text-gray-600">실시간 AI 자세 분석으로 정확한 운동을 시작하세요</p>
      </div>

      {!isSessionActive ? (
        <Card className="max-w-2xl mx-auto text-center py-12">
          <h2 className="text-2xl font-semibold mb-4">운동 준비</h2>
          <p className="text-gray-600 mb-6">운동을 선택하고 시작 버튼을 눌러주세요</p>

          {/* AI 추천 목표 배지 */}
          {targetSets != null && targetReps != null && (
            <div className="mb-6 mx-auto max-w-xs bg-blue-50 border border-blue-200 rounded-xl px-4 py-3">
              <p className="text-sm text-blue-700 font-medium">
                🎯 AI 추천 목표: {EXERCISE_NAMES[exercise]} {targetSets}세트 × {targetReps}회
              </p>
              <p className="text-xs text-blue-500 mt-1">
                총 {targetSets * targetReps}회 — KVS가 진행도를 추적합니다
              </p>
            </div>
          )}

          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-2">운동 선택</label>
            <select
              value={exercise}
              onChange={(e) => setExercise(e.target.value)}
              className="w-full max-w-xs mx-auto px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {exercises.map((ex) => (
                <option key={ex.value} value={ex.value}>{ex.label}</option>
              ))}
            </select>
          </div>

          <Button onClick={handleStartSession} size="lg">
            운동 시작
          </Button>
        </Card>
      ) : (
        <div className="grid md:grid-cols-3 gap-6">
          {/* Left: camera + controls */}
          <div className="md:col-span-2 space-y-4">
            <VideoFeed
              isActive={isSessionActive}
              onFrame={handleFrameCapture}
              exercise={exercise}
              landmarks={landmarks}
            />

            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <select
                  value={exercise}
                  onChange={(e) => setExercise(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {exercises.map((ex) => (
                    <option key={ex.value} value={ex.value}>{ex.label}</option>
                  ))}
                </select>

                <div className="font-mono text-lg font-semibold text-gray-700">
                  {formatTime(elapsedSeconds)}
                </div>
              </div>

              <Button onClick={handleEndSession} variant="danger" size="lg">
                운동 종료
              </Button>
            </div>
          </div>

          {/* Right: stats panel */}
          <div className="space-y-4">
            <RepCounter
              count={repCount}
              exercise={exercise}
              targetReps={targetReps ?? undefined}
              targetSets={targetSets ?? undefined}
            />

            {/* AI 추천 목표 진행도 */}
            {targetSets != null && targetReps != null && (
              <Card>
                <h3 className="font-semibold mb-2">목표 진행도</h3>
                <p className="text-sm text-gray-600 mb-2">
                  {repCount} / {targetSets * targetReps}회
                  ({Math.min(100, Math.round((repCount / (targetSets * targetReps)) * 100))}%)
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all"
                    style={{ width: `${Math.min(100, Math.round((repCount / (targetSets * targetReps)) * 100))}%` }}
                  />
                </div>
              </Card>
            )}

            <PostureFeedback analysis={analysis} />

            <Card>
              <h3 className="font-semibold mb-3">분석 상태</h3>
              <div className="flex items-center space-x-2 mb-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'AI 분석 중' : '연결 대기 중'}
                </span>
              </div>
              {analysis && (
                <div className="mt-2 p-2 bg-blue-50 rounded-lg">
                  <p className="text-xs text-blue-700 font-medium">
                    현재 점수: {analysis.formScore.toFixed(1)}점
                  </p>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

export default function WorkoutPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    }>
      <WorkoutContent />
    </Suspense>
  );
}
