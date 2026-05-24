'use client';

import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { ChevronLeftIcon, ChartBarIcon } from '@heroicons/react/24/outline';

export default function BodyInfoPage() {
  const router = useRouter();

  // Mock data - 실제로는 API에서 가져와야 함
  const bodyData = {
    weight: 70.5,
    muscleMass: 32.4,
    bodyFat: 15.2,
    bmi: 23.0,
    bodyWater: 52.1,
    boneMass: 3.2,
    visceralFat: 8,
  };

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
                  <p className="text-2xl font-bold">{bodyData.bmi}</p>
                </div>
              </div>
            </div>

            {/* Detailed Metrics */}
            <div className="bg-white rounded-3xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                상세 지표
              </h3>
              <div className="space-y-4">
                <MetricRow
                  label="골격근량"
                  value={`${bodyData.muscleMass} kg`}
                  percentage={78}
                  status="good"
                />
                <MetricRow
                  label="체지방률"
                  value={`${bodyData.bodyFat}%`}
                  percentage={15}
                  status="good"
                />
                <MetricRow
                  label="체수분"
                  value={`${bodyData.bodyWater}%`}
                  percentage={52}
                  status="normal"
                />
                <MetricRow
                  label="골무기질"
                  value={`${bodyData.boneMass} kg`}
                  percentage={85}
                  status="good"
                />
                <MetricRow
                  label="내장지방 레벨"
                  value={`${bodyData.visceralFat}`}
                  percentage={8}
                  status="good"
                />
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
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
