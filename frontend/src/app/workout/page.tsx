'use client';

import { Suspense, useState, useEffect, useRef, useCallback } from 'react';
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

  // ── session state ─────────────────────────────────────────────────────────
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [exercise, setExercise] = useState('squat');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const scoreHistoryRef = useRef<number[]>([]);
  const rdsSessionIdRef = useRef<string | null>(null);

  // ── AI recommendation targets ─────────────────────────────────────────────
  const [targetSets, setTargetSets] = useState<number | null>(null);
  const [targetReps, setTargetReps] = useState<number | null>(null);
  const recommendationIdRef = useRef<string | null>(null);

  // ── Set management ────────────────────────────────────────────────────────
  const [currentSet, setCurrentSet] = useState(1);
  const [restCountdown, setRestCountdown] = useState(0);
  const [setBaseCount, setSetBaseCount] = useState(0); // repCount/holdSeconds at start of current set
  const restActiveRef = useRef(false);
  const setCompletionFiredRef = useRef(false);

  // ── Agent feedback ────────────────────────────────────────────────────────
  const [agentFeedback, setAgentFeedback] = useState<string | null>(null);
  const [agentLoading, setAgentLoading] = useState(false);
  const recentIssuesRef = useRef<string[]>([]);

  // ── Posture WebSocket ─────────────────────────────────────────────────────
  const {
    connect,
    disconnect,
    sendFrame,
    analysis,
    landmarks,
    repCount,
    holdSeconds,
    isConnected,
    poseDetected,
  } = usePostureAnalysis();

  const repCountRef = useRef(0);
  const holdSecondsRef = useRef(0);
  useEffect(() => { repCountRef.current = repCount; }, [repCount]);
  useEffect(() => { holdSecondsRef.current = holdSeconds; }, [holdSeconds]);

  const isPlank = exercise === 'plank';
  const effectiveCount = isPlank ? holdSeconds : repCount;
  const currentSetCount = Math.max(0, effectiveCount - setBaseCount);

  // ── URL params ────────────────────────────────────────────────────────────
  useEffect(() => {
    const qEx = searchParams.get('exercise');
    const qSets = searchParams.get('sets');
    const qReps = searchParams.get('reps');
    const qRecId = searchParams.get('recommendationId');
    if (qEx && EXERCISE_NAMES[qEx]) setExercise(qEx);
    if (qSets) setTargetSets(parseInt(qSets, 10) || null);
    if (qReps) setTargetReps(parseInt(qReps, 10) || null);
    if (qRecId) recommendationIdRef.current = qRecId;
  }, [searchParams]);

  useEffect(() => {
    if (!isAuthenticated) router.push('/login');
  }, [isAuthenticated, router]);

  // ── Accumulate scores ─────────────────────────────────────────────────────
  useEffect(() => {
    if (analysis && isSessionActive && poseDetected) {
      scoreHistoryRef.current.push(analysis.formScore);
    }
    // Track recent issues for agent feedback
    if (analysis?.feedback && analysis.feedback.length > 0) {
      recentIssuesRef.current = analysis.feedback.slice(0, 5);
    }
  }, [analysis, isSessionActive, poseDetected]);

  // ── Session timer ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (isSessionActive) {
      timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      setElapsedSeconds(0);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [isSessionActive]);

  // ── Rest countdown ────────────────────────────────────────────────────────
  useEffect(() => {
    if (restCountdown <= 0) return;
    const timer = setTimeout(() => {
      setRestCountdown((prev) => {
        const next = prev - 1;
        if (next <= 0) {
          // Start next set
          const base = isPlank ? holdSecondsRef.current : repCountRef.current;
          setSetBaseCount(base);
          setCurrentSet((s) => s + 1);
          restActiveRef.current = false;
          setCompletionFiredRef.current = false;
          toast.success('다음 세트 시작!');
        }
        return next;
      });
    }, 1000);
    return () => clearTimeout(timer);
  }, [restCountdown, isPlank]);

  // ── Set completion detection ──────────────────────────────────────────────
  useEffect(() => {
    if (!targetReps || !targetSets || !isSessionActive) return;
    if (restActiveRef.current || setCompletionFiredRef.current) return;
    if (currentSet > targetSets) return; // all sets done

    if (currentSetCount >= targetReps) {
      setCompletionFiredRef.current = true;
      restActiveRef.current = true;

      if (currentSet < targetSets) {
        toast(`세트 ${currentSet} 완료! 10초 휴식합니다.`, { icon: '💪' });
        setRestCountdown(10);
        // Call agent for feedback after this set
        requestAgentFeedback();
      } else {
        toast.success('🎉 모든 세트를 완료했습니다!', { duration: 4000 });
        requestAgentFeedback();
      }
    }
  }, [currentSetCount, targetReps, targetSets, currentSet, isSessionActive]);

  // ── Agent feedback call ───────────────────────────────────────────────────
  const requestAgentFeedback = useCallback(async () => {
    if (!sessionId || !user?.userId || agentLoading) return;
    setAgentLoading(true);
    try {
      const result = await (apiClient as any).getPostureFeedback({
        user_id: user.userId,
        session_id: sessionId,
        exercise_name: exercise,
        posture_score: analysis ? analysis.formScore / 10 : 5,
        detected_issues: recentIssuesRef.current,
      });
      const feedback = (result as any)?.feedback || (result as any)?.data?.feedback;
      if (feedback) setAgentFeedback(feedback);
    } catch (e) {
      console.warn('Agent feedback failed:', e);
    } finally {
      setAgentLoading(false);
    }
  }, [sessionId, user, exercise, analysis, agentLoading]);

  // ── Session start ─────────────────────────────────────────────────────────
  const handleStartSession = async () => {
    if (!user) return;
    const sid = `${user.userId}-${Date.now()}`;
    setSessionId(sid);
    scoreHistoryRef.current = [];
    rdsSessionIdRef.current = null;
    setCurrentSet(1);
    setRestCountdown(0);
    setSetBaseCount(0);
    restActiveRef.current = false;
    setCompletionFiredRef.current = false;
    setAgentFeedback(null);

    try {
      await connect(sid);
    } catch {
      toast.error('자세 분석 서버에 연결할 수 없습니다.');
      setSessionId(null);
      return;
    }

    apiClient.startFreeSession().then((res: any) => {
      if (res?.id) rdsSessionIdRef.current = res.id;
    }).catch(() => {});

    setIsSessionActive(true);
    toast.success('운동 세션이 시작되었습니다!');
  };

  // ── Session end ───────────────────────────────────────────────────────────
  const handleEndSession = async () => {
    disconnect();
    setIsSessionActive(false);

    const scores = scoreHistoryRef.current;
    const avgScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
    const durationSec = elapsedSeconds;
    const durationMin = Math.max(1, Math.round(durationSec / 60));
    const totalActual = isPlank ? holdSeconds : repCount;
    const completedSetsCount = targetReps ? Math.floor(totalActual / targetReps) : 0;

    const hasTarget = targetSets != null && targetReps != null;
    const targetTotal = hasTarget ? targetSets! * targetReps! : null;
    const progressPercent = targetTotal ? Math.min(100, Math.round((totalActual / targetTotal) * 100)) : null;

    const sessionReport = {
      sessionId,
      completedAt: new Date().toISOString(),
      exercise,
      exerciseName: EXERCISE_NAMES[exercise] || exercise,
      isPlank,
      totalReps: isPlank ? repCount : repCount,
      holdSeconds: isPlank ? holdSeconds : undefined,
      totalActual,
      durationSeconds: durationSec,
      durationMinutes: durationMin,
      avgScore,
      recommendationId: recommendationIdRef.current,
      target: hasTarget ? { sets: targetSets, reps: targetReps, totalReps: targetTotal } : null,
      progress: progressPercent != null ? { percent: progressPercent, completedSets: completedSetsCount, completedReps: totalActual } : null,
      summary: {
        totalDuration: durationSec,     // seconds (not minutes)
        totalReps: totalActual,
        averagePostureScore: avgScore,
        completedSets: completedSetsCount,
      },
      exercises: [
        {
          name: EXERCISE_NAMES[exercise] || exercise,
          exercise,
          isPlank,
          sets: completedSetsCount || (hasTarget ? targetSets : 1),
          reps: isPlank ? 0 : repCount,
          holdSeconds: isPlank ? holdSeconds : undefined,
          targetSets,
          targetReps,
          progressPercent,
          duration: durationMin,
          postureScore: avgScore,
          notes: avgScore >= 85 ? '훌륭한 자세를 유지했습니다!' : avgScore >= 70 ? '전반적으로 좋은 자세였습니다.' : '자세 교정에 집중이 필요합니다.',
          agentFeedback: agentFeedback || undefined,
        },
      ],
      insights: [
        hasTarget
          ? isPlank
            ? `목표 ${targetSets}세트 × ${targetReps}초(총 ${targetTotal}초) 중 ${holdSeconds}초 유지 (${progressPercent}% 달성).`
            : `목표 ${targetSets}세트 × ${targetReps}회(총 ${targetTotal}회) 중 ${repCount}회 완료 (${progressPercent}% 달성).`
          : isPlank
          ? `총 ${holdSeconds}초 동안 플랭크를 유지했습니다.`
          : `총 ${repCount}회의 ${EXERCISE_NAMES[exercise]}를 완료했습니다.`,
        `평균 자세 점수 ${avgScore.toFixed(1)}점 (${avgScore >= 80 ? '우수' : avgScore >= 60 ? '양호' : '개선 필요'}).`,
        durationSec >= 60
          ? `${durationMin}분 동안 운동했습니다.`
          : `${durationSec}초 동안 운동했습니다.`,
      ],
      recommendations: avgScore >= 85
        ? ['자세가 좋습니다. 세트 수 또는 횟수를 늘려보세요.']
        : [`${EXERCISE_NAMES[exercise]} 시 자세를 더 신경써보세요.`, '거울 앞에서 자세를 확인하며 운동하면 도움이 됩니다.'],
    };

    // Update localStorage recommendation progress
    if (recommendationIdRef.current && typeof window !== 'undefined') {
      const progressKey = `gympt_rec_progress_${recommendationIdRef.current}`;
      try {
        const existing = JSON.parse(localStorage.getItem(progressKey) || '{}');
        const exProgress = existing.exercises || {};
        exProgress[exercise] = {
          done: true,
          completedAt: new Date().toISOString(),
          totalReps: totalActual,
          holdSeconds: isPlank ? holdSeconds : undefined,
          postureScore: Math.round(avgScore * 10) / 10,
          targetReps,
          targetSets,
        };
        const allDone = Object.values(exProgress).every((e: any) => e.done);
        localStorage.setItem(progressKey, JSON.stringify({
          recommendationId: recommendationIdRef.current,
          exercises: exProgress,
          startedAt: existing.startedAt || new Date().toISOString(),
          completedAt: allDone ? new Date().toISOString() : null,
        }));
      } catch { /* ignore */ }
    }

    const persistKey = rdsSessionIdRef.current || sessionId;
    if (typeof window !== 'undefined') {
      localStorage.setItem(`gympt_session_${persistKey}`, JSON.stringify({ ...sessionReport, sessionId: persistKey }));
    }

    if (rdsSessionIdRef.current) {
      apiClient.completeSession(rdsSessionIdRef.current, {
        totalDuration: durationSec,
        exerciseType: exercise,
        exerciseName: EXERCISE_NAMES[exercise] || exercise,
        totalReps: repCount,
        avgPostureScore: Math.round(avgScore * 100) / 100,
        ...(recommendationIdRef.current ? { recommendationId: recommendationIdRef.current } : {}),
      }).catch(() => {});
      rdsSessionIdRef.current = null;
    }

    toast.success('운동 완료! 리포트를 생성합니다...');
    setTimeout(() => router.push(`/report/detail?sessionId=${persistKey}`), 1200);
  };

  const handleFrameCapture = (frame: string) => {
    if (isConnected && sessionId) sendFrame(frame, exercise);
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

  const totalTarget = targetSets && targetReps ? targetSets * targetReps : null;
  const overallProgress = totalTarget ? Math.min(100, Math.round((effectiveCount / totalTarget) * 100)) : null;

  if (!user) return null;

  return (
    <div className="container mx-auto px-3 py-4 max-w-6xl">
      <div className="mb-4">
        <h1 className="text-2xl font-bold">운동 세션</h1>
        <p className="text-gray-500 text-sm">실시간 AI 자세 분석</p>
      </div>

      {!isSessionActive ? (
        /* ── 세션 시작 전 ── */
        <Card className="max-w-2xl mx-auto text-center py-10">
          <h2 className="text-2xl font-semibold mb-4">운동 준비</h2>
          <p className="text-gray-600 mb-6">운동을 선택하고 시작 버튼을 눌러주세요</p>

          {targetSets != null && targetReps != null && (
            <div className="mb-6 mx-auto max-w-xs bg-blue-50 border border-blue-200 rounded-xl px-4 py-3">
              <p className="text-sm text-blue-700 font-medium">
                🎯 AI 추천 목표: {EXERCISE_NAMES[exercise]} {targetSets}세트 ×{' '}
                {exercise === 'plank' ? `${targetReps}초` : `${targetReps}회`}
              </p>
              <p className="text-xs text-blue-500 mt-1">
                총 {exercise === 'plank' ? `${targetSets * targetReps}초` : `${targetSets * targetReps}회`}
                {' '} — 세트 완료 후 10초 휴식 자동 제공
              </p>
            </div>
          )}

          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-2">운동 선택</label>
            <select
              value={exercise}
              onChange={(e) => setExercise(e.target.value)}
              className="w-full max-w-xs mx-auto px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {exercises.map((ex) => <option key={ex.value} value={ex.value}>{ex.label}</option>)}
            </select>
          </div>

          <Button onClick={handleStartSession} size="lg">운동 시작</Button>
        </Card>
      ) : (
        /* ── 세션 활성 ── */
        <div className="grid lg:grid-cols-5 gap-4">
          {/* Left: Camera (60%) */}
          <div className="lg:col-span-3 space-y-3">
            <VideoFeed
              isActive={isSessionActive}
              onFrame={handleFrameCapture}
              exercise={exercise}
              landmarks={landmarks}
            />

            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <select
                  value={exercise}
                  onChange={(e) => setExercise(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                >
                  {exercises.map((ex) => <option key={ex.value} value={ex.value}>{ex.label}</option>)}
                </select>
                <div className="font-mono text-lg font-semibold text-gray-700">
                  {formatTime(elapsedSeconds)}
                </div>
              </div>
              <Button onClick={handleEndSession} variant="danger">운동 종료</Button>
            </div>
          </div>

          {/* Right: Stats panel (40%) */}
          <div className="lg:col-span-2 space-y-3">
            {/* Set counter + rep counter */}
            <RepCounter
              count={repCount}
              exercise={exercise}
              targetReps={targetReps ?? undefined}
              targetSets={targetSets ?? undefined}
              holdSeconds={holdSeconds}
              currentSet={currentSet}
              restCountdown={restCountdown}
              currentSetReps={isPlank ? undefined : currentSetCount}
            />

            {/* Overall progress (if AI target) */}
            {totalTarget != null && overallProgress != null && (
              <Card>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">전체 목표 달성도</h3>
                <p className="text-xs text-gray-500 mb-1.5">
                  {isPlank ? `${effectiveCount}초 / ${totalTarget}초` : `${effectiveCount}회 / ${totalTarget}회`}
                  {' '}({overallProgress}%)
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${overallProgress >= 100 ? 'bg-green-500' : 'bg-blue-600'}`}
                    style={{ width: `${overallProgress}%` }}
                  />
                </div>
              </Card>
            )}

            {/* Agent feedback */}
            {(agentFeedback || agentLoading) && (
              <Card>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-base">🤖</span>
                  <h3 className="text-sm font-semibold text-purple-700">AI 코치 피드백</h3>
                  {agentLoading && (
                    <div className="ml-auto animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500" />
                  )}
                </div>
                {agentFeedback && (
                  <p className="text-xs text-gray-700 leading-relaxed whitespace-pre-wrap">{agentFeedback}</p>
                )}
                {agentLoading && !agentFeedback && (
                  <p className="text-xs text-gray-400">AI가 자세를 분석하고 있습니다...</p>
                )}
              </Card>
            )}

            <PostureFeedback analysis={analysis} />

            {/* Connection status */}
            <Card>
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">{isConnected ? 'AI 자세 분석 중' : '연결 대기 중'}</span>
                {analysis && (
                  <span className="ml-auto text-xs font-semibold text-blue-600">
                    {analysis.formScore.toFixed(1)}점
                  </span>
                )}
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

export default function WorkoutPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" /></div>}>
      <WorkoutContent />
    </Suspense>
  );
}
