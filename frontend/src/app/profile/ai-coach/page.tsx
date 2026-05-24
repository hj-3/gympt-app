'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import {
  ChevronLeftIcon,
  SparklesIcon,
  FireIcon,
  ChartBarIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';

export default function AICoachPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  // Mock AI recommendations
  const recommendations = [
    {
      id: 1,
      category: 'workout',
      title: '상체 근력 강화 필요',
      description: '최근 운동 분석 결과, 하체에 비해 상체 근력이 부족합니다. 벤치프레스와 풀업 운동을 주 2-3회 추가하는 것을 권장합니다.',
      priority: 'high',
      icon: FireIcon,
    },
    {
      id: 2,
      category: 'posture',
      title: '스쿼트 자세 개선',
      description: '스쿼트 시 무릎이 발끝보다 앞으로 나가는 경향이 있습니다. 엉덩이를 더 뒤로 빼고 무게중심을 발뒤꿈치에 두세요.',
      priority: 'medium',
      icon: ChartBarIcon,
    },
    {
      id: 3,
      category: 'nutrition',
      title: '단백질 섭취 증가',
      description: '근육 성장을 위해 일일 체중 1kg당 1.6-2.0g의 단백질 섭취가 필요합니다. 현재 섭취량이 부족할 수 있으니 닭가슴살, 계란, 프로틴 쉐이크 등을 추가하세요.',
      priority: 'medium',
      icon: LightBulbIcon,
    },
  ];

  const handleGetNewRecommendation = async () => {
    setLoading(true);
    // TODO: Call AI Agent API
    await new Promise(resolve => setTimeout(resolve, 2000));
    setLoading(false);
    alert('새로운 추천을 받았습니다!');
  };

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
              AI 코치 추천
            </h1>
          </div>

          {/* Content */}
          <div className="px-4 py-6 space-y-4">
            {/* AI Coach Intro */}
            <div className="bg-gradient-to-br from-purple-500 to-blue-600 rounded-3xl p-6 shadow-lg text-white">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-12 h-12 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                  <SparklesIcon className="w-7 h-7" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">AI 코치</h2>
                  <p className="text-sm opacity-90">맞춤형 운동 가이드</p>
                </div>
              </div>
              <p className="text-sm opacity-90 leading-relaxed">
                AI가 회원님의 운동 데이터와 체성분 정보를 분석하여 개인 맞춤형 운동 및 영양 조언을 제공합니다.
              </p>
            </div>

            {/* Get New Recommendation */}
            <button
              onClick={handleGetNewRecommendation}
              disabled={loading}
              className="w-full bg-blue-600 text-white rounded-2xl p-4 shadow-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                  <span className="font-medium">분석 중...</span>
                </>
              ) : (
                <>
                  <SparklesIcon className="w-5 h-5" />
                  <span className="font-medium">새로운 추천 받기</span>
                </>
              )}
            </button>

            {/* Recommendations List */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-900 px-1">
                최근 추천 사항
              </h3>
              {recommendations.map((rec) => (
                <RecommendationCard key={rec.id} recommendation={rec} />
              ))}
            </div>

            {/* Stats */}
            <div className="bg-white rounded-3xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                AI 코치 활동
              </h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-blue-600">12</p>
                  <p className="text-xs text-gray-600 mt-1">총 추천</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-600">8</p>
                  <p className="text-xs text-gray-600 mt-1">완료</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-orange-600">4</p>
                  <p className="text-xs text-gray-600 mt-1">진행 중</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function RecommendationCard({ recommendation }: { recommendation: any }) {
  const Icon = recommendation.icon;
  const priorityColors = {
    high: 'bg-red-50 border-red-200',
    medium: 'bg-orange-50 border-orange-200',
    low: 'bg-blue-50 border-blue-200',
  };

  const priorityLabels = {
    high: '높음',
    medium: '보통',
    low: '낮음',
  };

  const priorityTextColors = {
    high: 'text-red-700',
    medium: 'text-orange-700',
    low: 'text-blue-700',
  };

  return (
    <div className={`bg-white rounded-3xl p-5 shadow-sm border-2 ${priorityColors[recommendation.priority as keyof typeof priorityColors]}`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
          <Icon className="w-6 h-6 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-base font-semibold text-gray-900">
              {recommendation.title}
            </h4>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${priorityTextColors[recommendation.priority as keyof typeof priorityTextColors]} bg-opacity-20`}>
              {priorityLabels[recommendation.priority as keyof typeof priorityLabels]}
            </span>
          </div>
          <p className="text-sm text-gray-600 leading-relaxed">
            {recommendation.description}
          </p>
          <button className="mt-3 text-sm text-blue-600 font-medium hover:text-blue-700">
            자세히 보기 →
          </button>
        </div>
      </div>
    </div>
  );
}
