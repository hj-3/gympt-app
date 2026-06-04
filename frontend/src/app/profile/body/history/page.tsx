'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { ChevronLeftIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { apiClient } from '@/lib/api-client';


interface BodyData {
  id: string;
  weight: number;
  height: number;
  muscleMass?: number;
  bodyFat?: number;
  measurementDate: string;
}

export default function BodyHistoryPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<BodyData[]>([]);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const response = await apiClient.getBodyProfileHistory() as any;
      const items: BodyData[] = Array.isArray(response)
        ? response
        : response?.items ?? response?.data ?? [];

      if (items.length > 0) {
        setHistory(items);
        setLoading(false);
        return;
      }
    } catch {
      // fall through to localStorage
    }

    // localStorage fallback
    try {
      const local = localStorage.getItem('gympt_body_history');
      if (local) setHistory(JSON.parse(local));
    } catch { /* ignore */ }
    setLoading(false);
  };

  const calculateBMI = (weight: number, height: number) => {
    const heightInMeters = height / 100;
    return (weight / (heightInMeters * heightInMeters)).toFixed(1);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
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

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center">
            <button
              onClick={() => router.back()}
              className="p-2 -ml-2 hover:bg-gray-100 rounded-full"
            >
              <ChevronLeftIcon className="w-6 h-6 text-gray-700" />
            </button>
            <h1 className="flex-1 text-lg font-semibold text-gray-900 text-center mr-10">
              측정 이력
            </h1>
          </div>

          {/* Content */}
          <div className="px-4 py-6 space-y-4">
            {history.length > 0 ? (
              history.map((record, index) => (
                <div
                  key={record.id}
                  className="bg-white rounded-3xl p-6 shadow-sm"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-3 bg-blue-100 rounded-2xl">
                        <ChartBarIcon className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-gray-900">
                          {formatDate(record.measurementDate)}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {index === 0 && '최신 측정'}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <MetricCard label="체중" value={`${record.weight}kg`} />
                    <MetricCard
                      label="BMI"
                      value={calculateBMI(record.weight, record.height)}
                    />
                    <MetricCard label="키" value={`${record.height}cm`} />
                    {record.bodyFat && (
                      <MetricCard label="체지방률" value={`${record.bodyFat}%`} />
                    )}
                    {record.muscleMass && (
                      <MetricCard
                        label="골격근량"
                        value={`${record.muscleMass}kg`}
                      />
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white rounded-3xl p-12 shadow-sm text-center">
                <ChartBarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  측정 이력이 없습니다
                </h3>
                <p className="text-sm text-gray-500">
                  인바디 데이터를 추가해주세요
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-gray-50 rounded-2xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
    </div>
  );
}
