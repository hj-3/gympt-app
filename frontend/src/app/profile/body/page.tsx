'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { ChevronLeftIcon, ChartBarIcon, PlusIcon } from '@heroicons/react/24/outline';
import { apiClient } from '@/lib/api-client';
import toast from 'react-hot-toast';

interface BodyData {
  id: string;
  weight: number;
  height: number;
  muscleMass?: number;
  bodyFat?: number;
  measurementDate: string;
}

export default function BodyInfoPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [bodyData, setBodyData] = useState<BodyData | null>(null);

  useEffect(() => {
    loadLatestBodyProfile();
  }, []);

  const loadLatestBodyProfile = async () => {
    try {
      setLoading(true);
      const response = await apiClient.getLatestBodyProfile();
      console.log('Body profile response:', response);
      if (response) {
        setBodyData(response);
      }
    } catch (error: any) {
      if (error.response?.status !== 404) {
        console.error('Failed to load body profile:', error);
        toast.error('인바디 정보를 불러오는데 실패했습니다');
      }
    } finally {
      setLoading(false);
    }
  };

  const calculateBMI = (weight: number, height: number) => {
    const heightInMeters = height / 100;
    return (weight / (heightInMeters * heightInMeters)).toFixed(1);
  };

  const calculatePercentage = (value: number, max: number) => {
    return Math.min((value / max) * 100, 100);
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
              인바디 정보
            </h1>
          </div>

          {/* Content */}
          <div className="px-4 py-6 space-y-4">
            {bodyData ? (
              <>
                {/* Summary Card */}
                <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl p-6 shadow-lg text-white">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold">체성분 분석</h2>
                    <ChartBarIcon className="w-8 h-8 opacity-80" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm opacity-80">체중</p>
                      <p className="text-2xl font-bold">{bodyData.weight} kg</p>
                    </div>
                    <div>
                      <p className="text-sm opacity-80">BMI</p>
                      <p className="text-2xl font-bold">
                        {calculateBMI(bodyData.weight, bodyData.height)}
                      </p>
                    </div>
                  </div>
                  <p className="text-xs opacity-70 mt-4">
                    측정일: {new Date(bodyData.measurementDate).toLocaleDateString('ko-KR')}
                  </p>
                </div>

                {/* Detailed Metrics */}
                <div className="bg-white rounded-3xl p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    상세 지표
                  </h3>
                  <div className="space-y-4">
                    <MetricRow
                      label="키"
                      value={`${bodyData.height} cm`}
                      percentage={calculatePercentage(bodyData.height, 200)}
                      status="normal"
                    />
                    {bodyData.muscleMass && (
                      <MetricRow
                        label="골격근량"
                        value={`${bodyData.muscleMass} kg`}
                        percentage={calculatePercentage(bodyData.muscleMass, 50)}
                        status="good"
                      />
                    )}
                    {bodyData.bodyFat && (
                      <MetricRow
                        label="체지방률"
                        value={`${bodyData.bodyFat}%`}
                        percentage={bodyData.bodyFat}
                        status={bodyData.bodyFat < 20 ? 'good' : bodyData.bodyFat < 25 ? 'normal' : 'warning'}
                      />
                    )}
                  </div>
                </div>

                {/* History Button */}
                <button
                  onClick={() => router.push('/profile/body/history')}
                  className="w-full bg-white rounded-2xl p-4 shadow-sm hover:bg-gray-50 transition-colors"
                >
                  <span className="text-base font-medium text-gray-900">
                    측정 이력 보기
                  </span>
                </button>
              </>
            ) : (
              // Empty State
              <div className="bg-white rounded-3xl p-12 shadow-sm text-center">
                <ChartBarIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  인바디 정보가 없습니다
                </h3>
                <p className="text-sm text-gray-500 mb-6">
                  첫 인바디 측정 데이터를 입력하세요
                </p>
                <button
                  onClick={() => router.push('/profile/body/add')}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 transition-colors"
                >
                  <PlusIcon className="w-5 h-5" />
                  <span>측정 데이터 추가</span>
                </button>
              </div>
            )}

            {/* Add New Button */}
            {bodyData && (
              <button
                onClick={() => router.push('/profile/body/add')}
                className="w-full bg-blue-600 text-white rounded-2xl p-4 shadow-sm hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <PlusIcon className="w-5 h-5" />
                <span className="font-medium">새 측정 데이터 추가</span>
              </button>
            )}

            {/* Info */}
            <div className="bg-blue-50 rounded-2xl p-4">
              <p className="text-sm text-blue-800">
                <span className="font-semibold">Tip:</span> 정확한 체성분 측정을 위해 매일 같은 시간에 측정하는 것을 권장합니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function MetricRow({
  label,
  value,
  percentage,
  status,
}: {
  label: string;
  value: string;
  percentage: number;
  status: 'good' | 'normal' | 'warning';
}) {
  const statusColors = {
    good: 'bg-green-500',
    normal: 'bg-blue-500',
    warning: 'bg-orange-500',
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm text-gray-600">{label}</span>
        <span className="text-sm font-semibold text-gray-900">{value}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${statusColors[status]}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}
