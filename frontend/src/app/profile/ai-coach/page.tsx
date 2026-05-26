'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api-client';
import {
  ChevronLeftIcon,
  SparklesIcon,
  FireIcon,
  ChartBarIcon,
  LightBulbIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Recommendation {
  title: string;
  content: string;
  category: string;
  createdAt: string;
}

export default function AICoachPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    goal: 'weight_loss',
    fitness_level: 'intermediate',
    days_per_week: 3,
    equipment_available: ['dumbbells', 'barbell'],
    injuries_or_limitations: '',
  });

  const handleGetNewRecommendation = async () => {
    if (!user?.userId) {
      toast.error('사용자 정보를 찾을 수 없습니다');
      return;
    }

    setLoading(true);
    try {
      // Load body profile to enhance recommendation
      let bodyProfile = null;
      try {
        const bodyResponse = await apiClient.getLatestBodyProfile();
        bodyProfile = bodyResponse.data;
      } catch (err) {
        console.log('No body profile found, proceeding without it');
      }

      const response = await apiClient.getWorkoutRecommendation({
        user_id: user.userId,
        goal: formData.goal,
        fitness_level: formData.fitness_level,
        days_per_week: formData.days_per_week,
        equipment_available: formData.equipment_available,
        injuries_or_limitations: formData.injuries_or_limitations || undefined,
        // Add body profile data for better recommendations
        ...(bodyProfile && {
          height: bodyProfile.height,
          weight: bodyProfile.weight,
          body_fat: bodyProfile.bodyFat,
          muscle_mass: bodyProfile.muscleMass,
        }),
      });

      console.log('Recommendation response:', response);
      if (response) {
        toast.success('새로운 추천을 받았습니다!');
        // Agent service returns { recommendation: string, model_used: string, cached: boolean }
        const recommendationText = (response as any).recommendation || JSON.stringify(response);
        const newRec: Recommendation = {
          title: '맞춤 운동 프로그램',
          content: recommendationText,
          category: 'workout',
          createdAt: new Date().toISOString(),
        };
        setRecommendations([newRec, ...recommendations]);
        setShowForm(false);
      }
    } catch (error: any) {
      console.error('Failed to get recommendation:', error);
      toast.error('추천을 받는데 실패했습니다');
    } finally {
      setLoading(false);
    }
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
            {!showForm ? (
              <button
                onClick={() => setShowForm(true)}
                className="w-full bg-blue-600 text-white rounded-2xl p-4 shadow-sm hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <SparklesIcon className="w-5 h-5" />
                <span className="font-medium">새로운 추천 받기</span>
              </button>
            ) : (
              <div className="bg-white rounded-3xl p-6 shadow-sm space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  운동 목표 설정
                </h3>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    운동 목표
                  </label>
                  <select
                    value={formData.goal}
                    onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="weight_loss">체중 감량</option>
                    <option value="muscle_gain">근육 증가</option>
                    <option value="endurance">지구력 향상</option>
                    <option value="general_fitness">전반적인 건강</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    현재 운동 수준
                  </label>
                  <select
                    value={formData.fitness_level}
                    onChange={(e) => setFormData({ ...formData, fitness_level: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="beginner">초급</option>
                    <option value="intermediate">중급</option>
                    <option value="advanced">고급</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    주간 운동 횟수
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="7"
                    value={formData.days_per_week}
                    onChange={(e) => setFormData({ ...formData, days_per_week: parseInt(e.target.value) })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    부상 또는 제한사항
                  </label>
                  <textarea
                    value={formData.injuries_or_limitations}
                    onChange={(e) => setFormData({ ...formData, injuries_or_limitations: e.target.value })}
                    placeholder="예: 무릎 통증, 허리 디스크 등"
                    rows={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => setShowForm(false)}
                    className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
                  >
                    취소
                  </button>
                  <button
                    onClick={handleGetNewRecommendation}
                    disabled={loading}
                    className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                        <span>분석 중...</span>
                      </>
                    ) : (
                      <>
                        <SparklesIcon className="w-5 h-5" />
                        <span>추천 받기</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Recommendations List */}
            {recommendations.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-lg font-semibold text-gray-900 px-1">
                  최근 추천 사항
                </h3>
                {recommendations.map((rec, index) => (
                  <RecommendationCard key={index} recommendation={rec} />
                ))}
              </div>
            )}

            {recommendations.length === 0 && !showForm && (
              <div className="bg-white rounded-3xl p-12 shadow-sm text-center">
                <SparklesIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  추천 내역이 없습니다
                </h3>
                <p className="text-sm text-gray-500">
                  첫 AI 추천을 받아보세요
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const categoryIcons: Record<string, any> = {
    workout: FireIcon,
    posture: ChartBarIcon,
    nutrition: LightBulbIcon,
  };

  const Icon = categoryIcons[recommendation.category] || LightBulbIcon;

  return (
    <div className="bg-white rounded-3xl p-5 shadow-sm border-2 border-blue-100">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
          <Icon className="w-6 h-6 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-base font-semibold text-gray-900 mb-2">
            {recommendation.title}
          </h4>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
            {recommendation.content}
          </p>
          <p className="text-xs text-gray-400 mt-3">
            {new Date(recommendation.createdAt).toLocaleDateString('ko-KR')}
          </p>
        </div>
      </div>
    </div>
  );
}
