'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { apiClient } from '@/lib/api-client';
import {
  ChevronLeftIcon,
  TrophyIcon,
  FireIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmtDuration(seconds: number): string {
  if (!seconds || seconds < 60) return `${seconds || 0}초`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s > 0 ? `${m}분 ${s}초` : `${m}분`;
}

function fmtTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
}

// ── Sub-components ────────────────────────────────────────────────────────────

function ExerciseCard({ exercise }: { exercise: any }) {
  const isPlank = exercise.isPlank || exercise.exercise === 'plank';
  return (
    <div className="border-2 border-gray-100 rounded-2xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-900">{exercise.name || '운동'}</h4>
        <span className="text-sm font-bold text-blue-600">
          {exercise.postureScore?.toFixed(1) || '0.0'}점
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-gray-500 mb-1">세트</p>
          <p className="font-medium text-gray-900">{exercise.sets || 0}세트</p>
        </div>
        {isPlank ? (
          <div>
            <p className="text-gray-500 mb-1">유지 시간</p>
            <p className="font-medium text-gray-900">
              {fmtTime(exercise.holdSeconds ?? exercise.totalActual ?? 0)}
            </p>
          </div>
        ) : (
          <div>
            <p className="text-gray-500 mb-1">횟수</p>
            <p className="font-medium text-gray-900">{exercise.reps || exercise.totalActual || 0}회</p>
          </div>
        )}
        <div>
          <p className="text-gray-500 mb-1">시간</p>
          <p className="font-medium text-gray-900">{fmtDuration(exercise.durationSeconds || (exercise.duration || 0) * 60)}</p>
        </div>
      </div>

      {/* Target vs actual */}
      {exercise.targetReps != null && exercise.targetSets != null && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>목표 달성률</span>
            <span className="font-bold text-blue-600">{exercise.progressPercent ?? 0}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all ${(exercise.progressPercent ?? 0) >= 100 ? 'bg-green-500' : 'bg-blue-500'}`}
              style={{ width: `${Math.min(100, exercise.progressPercent ?? 0)}%` }}
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            목표: {exercise.targetSets}세트 × {isPlank ? `${exercise.targetReps}초` : `${exercise.targetReps}회`}
          </p>
        </div>
      )}

      {/* Agent feedback */}
      {exercise.agentFeedback && (
        <div className="mt-3 pt-3 border-t border-gray-100 bg-purple-50 rounded-xl p-3">
          <p className="text-xs font-semibold text-purple-700 mb-1">🤖 AI 코치 피드백</p>
          <p className="text-xs text-gray-700 leading-relaxed">{exercise.agentFeedback}</p>
        </div>
      )}

      {exercise.notes && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-600">{exercise.notes}</p>
        </div>
      )}
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────

function ReportDetailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('sessionId');
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    if (sessionId) loadReport();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const loadReport = async () => {
    setLoading(true);
    if (typeof window !== 'undefined') {
      const local = localStorage.getItem(`gympt_session_${sessionId}`);
      if (local) {
        try { setReport(JSON.parse(local)); setLoading(false); return; } catch {}
      }
    }
    try {
      const response = await apiClient.getReport(sessionId!) as any;
      setReport(response);
    } catch {
      setReport(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="flex flex-col items-center justify-center min-h-screen gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
          <p className="text-gray-500 text-sm">리포트 로딩 중...</p>
        </div>
      </ProtectedRoute>
    );
  }

  if (!report) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">리포트를 찾을 수 없습니다</h2>
            <button onClick={() => router.push('/report')} className="text-blue-600 hover:text-blue-700">
              목록으로 돌아가기
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  const summary = report.summary || {};
  const isPlankSession = report.isPlank || report.exercise === 'plank';

  // Support both new (durationSeconds) and old (totalDuration in minutes) formats
  const durationSec: number = summary.totalDuration > 300
    ? summary.totalDuration  // already in seconds (new format)
    : (summary.totalDuration || 0) * 60;  // old format was minutes

  const totalCount: number = summary.totalReps ?? report.totalActual ?? report.totalReps ?? 0;
  const avgScore: number = summary.averagePostureScore ?? 0;

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto pb-20">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center sticky top-0 z-10">
            <button onClick={() => router.push('/dashboard')} className="p-2 -ml-2 hover:bg-gray-100 rounded-full">
              <ChevronLeftIcon className="w-6 h-6 text-gray-700" />
            </button>
            <h1 className="flex-1 text-lg font-semibold text-gray-900 text-center mr-10">운동 리포트</h1>
          </div>

          <div className="px-4 py-6 space-y-5">
            {/* Summary Card */}
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl p-6 shadow-lg text-white">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm opacity-80 mb-1">완료</p>
                  <p className="text-base font-semibold">
                    {report.completedAt
                      ? new Date(report.completedAt).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })
                      : new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}
                  </p>
                </div>
                <TrophyIcon className="w-12 h-12 opacity-80" />
              </div>

              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/20">
                <div>
                  <p className="text-xs opacity-80 mb-1 flex items-center gap-1">
                    <ClockIcon className="w-3 h-3" />운동 시간
                  </p>
                  <p className="text-lg font-bold">{fmtDuration(durationSec)}</p>
                </div>
                <div>
                  <p className="text-xs opacity-80 mb-1">
                    {isPlankSession ? '유지 시간' : '총 횟수'}
                  </p>
                  <p className="text-lg font-bold">
                    {isPlankSession ? fmtTime(report.holdSeconds ?? totalCount) : `${totalCount}회`}
                  </p>
                </div>
                <div>
                  <p className="text-xs opacity-80 mb-1">평균 점수</p>
                  <p className="text-lg font-bold">{avgScore.toFixed(1)}</p>
                </div>
              </div>
            </div>

            {/* Recommendation target progress */}
            {report.target && report.progress && (
              <div className="bg-white rounded-3xl p-5 shadow-sm">
                <h3 className="text-base font-semibold text-gray-900 mb-3">추천 목표 달성도</h3>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">
                    목표 {report.target.sets}세트 × {isPlankSession ? `${report.target.reps}초` : `${report.target.reps}회`}
                    {' '}(총 {isPlankSession ? `${report.target.totalReps}초` : `${report.target.totalReps}회`})
                  </span>
                  <span className={`text-sm font-bold ${report.progress.percent >= 100 ? 'text-green-600' : 'text-blue-600'}`}>
                    {report.progress.percent}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                  <div
                    className={`h-3 rounded-full ${report.progress.percent >= 100 ? 'bg-green-500' : 'bg-blue-600'}`}
                    style={{ width: `${Math.min(100, report.progress.percent)}%` }}
                  />
                </div>
                <p className="text-sm text-gray-600">
                  {report.progress.percent >= 100
                    ? `🎉 목표 달성! (${isPlankSession ? `${report.totalActual}초` : `${report.totalActual}회`} 완료)`
                    : isPlankSession
                    ? `${report.holdSeconds ?? report.totalActual}초 완료 — 목표까지 ${report.target.totalReps - (report.holdSeconds ?? report.totalActual ?? 0)}초 남았습니다`
                    : `${report.totalActual}회 완료 — 목표까지 ${report.target.totalReps - report.totalActual}회 남았습니다`}
                </p>
              </div>
            )}

            {/* Exercise details */}
            {report.exercises?.length > 0 && (
              <div className="bg-white rounded-3xl p-5 shadow-sm">
                <h3 className="text-base font-semibold text-gray-900 mb-4">운동 상세</h3>
                <div className="space-y-4">
                  {report.exercises.map((ex: any, idx: number) => (
                    <ExerciseCard key={idx} exercise={ex} />
                  ))}
                </div>
              </div>
            )}

            {/* Insights */}
            {report.insights?.length > 0 && (
              <div className="bg-white rounded-3xl p-5 shadow-sm">
                <h3 className="text-base font-semibold text-gray-900 mb-3">분석 인사이트</h3>
                <div className="space-y-2">
                  {report.insights.map((insight: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-2 p-3 bg-blue-50 rounded-xl">
                      <CheckCircleIcon className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-gray-700">{insight}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {report.recommendations?.length > 0 && (
              <div className="bg-white rounded-3xl p-5 shadow-sm">
                <h3 className="text-base font-semibold text-gray-900 mb-3">개선 추천</h3>
                <div className="space-y-2">
                  {report.recommendations.map((rec: string, idx: number) => (
                    <div key={idx} className="flex items-start gap-2 p-3 bg-orange-50 rounded-xl">
                      <FireIcon className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-gray-700">{rec}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={() => router.push('/workout')}
              className="w-full bg-blue-600 text-white rounded-2xl p-4 font-medium hover:bg-blue-700 transition-colors"
            >
              다시 운동하기
            </button>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

export default function ReportDetailPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    }>
      <ReportDetailContent />
    </Suspense>
  );
}
