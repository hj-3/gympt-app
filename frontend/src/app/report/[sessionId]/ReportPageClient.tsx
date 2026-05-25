'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { apiClient } from '@/lib/api-client';
import {
  ChevronLeftIcon,
  TrophyIcon,
  FireIcon,
  ClockIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function ReportPageClient() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    if (sessionId) {
      loadReport();
    }
  }, [sessionId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getReport(sessionId);
      if (response.data) {
        setReport(response.data);
      }
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
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <p className="text-gray-600">리포트를 찾을 수 없습니다</p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg"
            >
              대시보드로 돌아가기
            </button>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  const summary = report.summary || {};

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto">
          <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center sticky top-0 z-10">
            <button
              onClick={() => router.push('/dashboard')}
              className="p-2 -ml-2 hover:bg-gray-100 rounded-full"
            >
              <ChevronLeftIcon className="w-6 h-6 text-gray-700" />
            </button>
            <h1 className="flex-1 text-lg font-semibold text-gray-900 text-center mr-10">
              운동 리포트
            </h1>
          </div>

          <div className="px-4 py-6 space-y-4">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl p-6 shadow-lg text-white">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold">운동 완료!</h2>
                <TrophyIcon className="w-10 h-10" />
              </div>
              <p className="text-sm opacity-90">
                {new Date(report.completedAt).toLocaleString('ko-KR')}
              </p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <SummaryCard
                icon={<ClockIcon className="w-5 h-5 text-blue-600" />}
                label="시간"
                value={`${summary.totalDuration || 0}분`}
              />
              <SummaryCard
                icon={<FireIcon className="w-5 h-5 text-orange-600" />}
                label="칼로리"
                value={`${summary.caloriesBurned || 0}`}
              />
              <SummaryCard
                icon={<TrophyIcon className="w-5 h-5 text-yellow-600" />}
                label="점수"
                value={`${summary.averagePostureScore?.toFixed(1) || 0}`}
              />
            </div>

            <div className="bg-white rounded-3xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                운동 상세
              </h3>
              {report.exerciseDetails && report.exerciseDetails.length > 0 ? (
                <div className="space-y-3">
                  {report.exerciseDetails.map((exercise: any, index: number) => (
                    <ExerciseDetail key={index} exercise={exercise} />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500 text-center py-4">
                  운동 상세 정보가 없습니다
                </p>
              )}
            </div>

            {report.insights && report.insights.length > 0 && (
              <div className="bg-white rounded-3xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  인사이트
                </h3>
                <ul className="space-y-2">
                  {report.insights.map((insight: string, index: number) => (
                    <li key={index} className="flex items-start gap-2">
                      <CheckCircleIcon className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-700">{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {report.recommendations && report.recommendations.length > 0 && (
              <div className="bg-blue-50 rounded-3xl p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  추천 사항
                </h3>
                <ul className="space-y-2">
                  {report.recommendations.map((rec: string, index: number) => (
                    <li key={index} className="text-sm text-blue-900">
                      • {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <button
              onClick={() => router.push('/dashboard')}
              className="w-full bg-blue-600 text-white rounded-2xl p-4 font-semibold hover:bg-blue-700 transition-colors"
            >
              대시보드로 돌아가기
            </button>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function SummaryCard({ icon, label, value }: any) {
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm text-center">
      <div className="flex justify-center mb-2">{icon}</div>
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className="text-lg font-bold text-gray-900">{value}</p>
    </div>
  );
}

function ExerciseDetail({ exercise }: any) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-900">{exercise.name}</p>
        <p className="text-xs text-gray-500">
          {exercise.sets}세트 × {exercise.reps}회
        </p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold text-blue-600">
          {exercise.avgPostureScore?.toFixed(1) || 0}점
        </p>
      </div>
    </div>
  );
}
