'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api-client';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function ReportListPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    if (user?.userId) {
      loadReports();
    }
  }, [user, page]);

  const loadReports = async () => {
    if (!user?.userId) return;

    try {
      setLoading(true);
      const response = await apiClient.getReports(user.userId, page, 10) as any;
      if (response) {
        setReports(response.items || []);
        setHasMore(response.hasMore || false);
      }
    } catch (error) {
      console.error('Failed to load reports:', error);
      toast.error('리포트 목록을 불러오는데 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto">
          <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center sticky top-0 z-10">
            <button
              onClick={() => router.back()}
              className="p-2 -ml-2 hover:bg-gray-100 rounded-full"
            >
              <ChevronLeftIcon className="w-6 h-6 text-gray-700" />
            </button>
            <h1 className="flex-1 text-lg font-semibold text-gray-900 text-center mr-10">
              운동 기록
            </h1>
          </div>

          <div className="px-4 py-6">
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : reports.length > 0 ? (
              <div className="space-y-3">
                {reports.map((report) => (
                  <Link
                    key={report.reportId}
                    href={`/report/${report.sessionId || report.reportId}`}
                  >
                    <div className="bg-white rounded-2xl p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer">
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-semibold text-gray-900">
                          {report.summary?.exercisesCompleted || 0}개 운동 완료
                        </p>
                        <ChevronRightIcon className="w-5 h-5 text-gray-400" />
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <p className="text-gray-600">
                          {new Date(report.completedAt).toLocaleDateString('ko-KR')}
                        </p>
                        <div className="flex items-center gap-3">
                          <span className="text-blue-600 font-semibold">
                            {report.summary?.averagePostureScore?.toFixed(1) || 0}점
                          </span>
                          <span className="text-gray-500">
                            {report.summary?.totalDuration || 0}분
                          </span>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
                {hasMore && (
                  <button
                    onClick={() => setPage(page + 1)}
                    className="w-full py-3 text-blue-600 font-medium hover:bg-blue-50 rounded-xl transition-colors"
                  >
                    더 보기
                  </button>
                )}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500 mb-4">아직 운동 기록이 없습니다</p>
                <button
                  onClick={() => router.push('/workout')}
                  className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
                >
                  운동 시작하기
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
