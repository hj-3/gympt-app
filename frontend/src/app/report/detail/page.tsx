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
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

function ReportDetailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('sessionId');
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    if (sessionId) {
      loadReport();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getReport(sessionId!);
      setReport(response.data);
    } catch (error: any) {
      console.error('Failed to load report:', error);
      toast.error('리포트를 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </ProtectedRoute>
    );
  }

  if (!report) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              리포트를 찾을 수 없습니다
            </h2>
            <button
              onClick={() => router.push('/report')}
              className="text-blue-600 hover:text-blue-700"
            >
              목록으로 돌아가기
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto pb-20">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center sticky top-0 z-10">
            <button
              onClick={() => router.back()}
              className="p-2 -ml-2 hover:bg-gray-100 rounded-full"
            >
              <ChevronLeftIcon className="w-6 h-6 text-gray-700" />
            </button>
            <h1 className="flex-1 text-lg font-semibold text-gray-900 text-center mr-10">
              운동 리포트
            </h1>
          </div>

          {/* Summary Card */}
          <div className="px-4 py-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl p-6 shadow-lg text-white mb-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm opacity-90 mb-1">완료 시간</p>
                  <p className="text-lg font-semibold">
                    {report.completedAt
                      ? new Date(report.completedAt).toLocaleDateString('ko-KR', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      : '-'}
                  </p>
                </div>
                <TrophyIcon className="w-12 h-12 opacity-80" />
              </div>

              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/20">
                <div>
                  <p className="text-xs opacity-80 mb-1">운동 시간</p>
                  <p className="text-xl font-bold">
                    {report.summary?.totalDuration || 0}분
                  </p>
                </div>
                <div>
                  <p className="text-xs opacity-80 mb-1">완료 운동</p>
                  <p className="text-xl font-bold">
                    {report.summary?.exercisesCompleted || 0}개
                  </p>
                </div>
                <div>
                  <p className="text-xs opacity-80 mb-1">평균 점수</p>
                  <p className="text-xl font-bold">
                    {report.summary?.averagePostureScore?.toFixed(1) || 0}
                  </p>
                </div>
              </div>
            </div>

            {/* Exercise Details */}
            {report.exercises && report.exercises.length > 0 && (
              <div className="bg-white rounded-3xl p-6 shadow-sm mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  운동 상세
                </h3>
                <div className="space-y-4">
                  {report.exercises.map((exercise: any, index: number) => (
                    <ExerciseCard key={index} exercise={exercise} />
                  ))}
                </div>
              </div>
            )}

            {/* Insights */}
            {report.insights && report.insights.length > 0 && (
              <div className="bg-white rounded-3xl p-6 shadow-sm mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  분석 인사이트
                </h3>
                <div className="space-y-3">
                  {report.insights.map((insight: string, index: number) => (
                    <div
                      key={index}
                      className="flex items-start gap-3 p-3 bg-blue-50 rounded-xl"
                    >
                      <CheckCircleIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-gray-700">{insight}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {report.recommendations && report.recommendations.length > 0 && (
              <div className="bg-white rounded-3xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  개선 추천
                </h3>
                <div className="space-y-3">
                  {report.recommendations.map((rec: string, index: number) => (
                    <div
                      key={index}
                      className="flex items-start gap-3 p-3 bg-orange-50 rounded-xl"
                    >
                      <FireIcon className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-gray-700">{rec}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function ExerciseCard({ exercise }: { exercise: any }) {
  return (
    <div className="border-2 border-gray-100 rounded-2xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-900">{exercise.name || '운동'}</h4>
        <span className="text-sm font-medium text-blue-600">
          {exercise.postureScore?.toFixed(1) || 0}점
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <p className="text-gray-500 mb-1">세트</p>
          <p className="font-medium text-gray-900">
            {exercise.sets || 0}세트
          </p>
        </div>
        <div>
          <p className="text-gray-500 mb-1">횟수</p>
          <p className="font-medium text-gray-900">
            {exercise.reps || 0}회
          </p>
        </div>
        <div>
          <p className="text-gray-500 mb-1">시간</p>
          <p className="font-medium text-gray-900">
            {exercise.duration || 0}분
          </p>
        </div>
      </div>

      {exercise.notes && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-600">{exercise.notes}</p>
        </div>
      )}
    </div>
  );
}

export default function ReportDetailPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    }>
      <ReportDetailContent />
    </Suspense>
  );
}
