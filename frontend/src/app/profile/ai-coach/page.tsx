'use client';

import { useState, useEffect } from 'react';
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
  PlayIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface TargetExercise {
  exercise: string;
  sets: number;
  reps: number;
}

interface ExerciseProgress {
  done: boolean;
  completedAt: string | null;
  totalReps: number;
  postureScore: number;
  targetReps: number | null;
  targetSets: number | null;
}

interface RecProgress {
  recommendationId: string;
  exercises: Record<string, ExerciseProgress>;
  startedAt: string;
  completedAt: string | null;
}

interface Recommendation {
  id?: string;
  title: string;
  content: string;
  category: string;
  createdAt: string;
  goal?: string;
  fitnessLevel?: string;
  targetExercises?: TargetExercise[];
}

function loadRecProgress(recommendationId: string): RecProgress | null {
  if (typeof window === 'undefined' || !recommendationId) return null;
  try {
    const raw = localStorage.getItem(`gympt_rec_progress_${recommendationId}`);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

// KVS-trackable exercise key -> 한국어 라벨 (/workout 과 동일)
const EXERCISE_LABELS: Record<string, string> = {
  squat: '스쿼트',
  pushup: '푸시업',
  lunge: '런지',
  plank: '플랭크',
};

// DB에 JSON 문자열로 저장된 target_exercises 를 파싱.
// KVS 추적 가능한 운동(EXERCISE_LABELS)만 통과시킨다.
function parseTargetExercises(raw: unknown): TargetExercise[] {
  if (!raw) return [];
  try {
    const arr = typeof raw === 'string' ? JSON.parse(raw) : raw;
    if (!Array.isArray(arr)) return [];
    return arr.filter(
      (t: any) =>
        t && EXERCISE_LABELS[t.exercise] && t.sets > 0 && t.reps > 0
    );
  } catch {
    return [];
  }
}

export default function AICoachPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    goal: 'weight_loss',
    fitness_level: 'intermediate',
    days_per_week: 3,
    equipment_available: ['dumbbells', 'barbell'],
    injuries_or_limitations: '',
  });

  // Load recommendation history once user auth is confirmed
  useEffect(() => {
    if (user) loadRecommendations();
  }, [user?.userId]);

  const loadRecommendations = async () => {
    try {
      setLoadingHistory(true);
      const response = await apiClient.getWorkoutRecommendations(10) as any;
      const items = Array.isArray(response) ? response : response?.data ?? [];
      if (items.length > 0) {
        const history = items.map((rec: any) => ({
          id: rec.id,
          title: '맞춤 운동 프로그램',
          content: rec.recommendation,
          category: 'workout',
          createdAt: rec.createdAt,
          goal: rec.goal,
          fitnessLevel: rec.fitnessLevel,
          targetExercises: parseTargetExercises(rec.targetExercises),
        }));
        setRecommendations(history);
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

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
        bodyProfile = await apiClient.getLatestBodyProfile() as any;
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
        // Reload recommendations from database
        await loadRecommendations();
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
            {loadingHistory ? (
              <div className="bg-white rounded-3xl p-12 shadow-sm text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
                <p className="text-sm text-gray-500">추천 내역을 불러오는 중...</p>
              </div>
            ) : recommendations.length > 0 ? (
              <div className="space-y-3">
                <h3 className="text-lg font-semibold text-gray-900 px-1">
                  최근 추천 사항
                </h3>
                {recommendations.map((rec, index) => (
                  <RecommendationCard key={rec.id || index} recommendation={rec} />
                ))}
              </div>
            ) : !showForm ? (
              <div className="bg-white rounded-3xl p-12 shadow-sm text-center">
                <SparklesIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  추천 내역이 없습니다
                </h3>
                <p className="text-sm text-gray-500">
                  첫 AI 추천을 받아보세요
                </p>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const router = useRouter();
  const [progress, setProgress] = useState<RecProgress | null>(null);

  useEffect(() => {
    if (recommendation.id) {
      setProgress(loadRecProgress(recommendation.id));
    }
  }, [recommendation.id]);

  const categoryIcons: Record<string, any> = {
    workout: FireIcon,
    posture: ChartBarIcon,
    nutrition: LightBulbIcon,
  };

  const Icon = categoryIcons[recommendation.category] || LightBulbIcon;
  const targets = recommendation.targetExercises ?? [];

  const startWorkout = (t: TargetExercise) => {
    const params = new URLSearchParams({
      exercise: t.exercise,
      sets: String(t.sets),
      reps: String(t.reps),
    });
    if (recommendation.id) params.set('recommendationId', recommendation.id);
    router.push(`/workout?${params.toString()}`);
  };

  const doneCount = progress
    ? Object.values(progress.exercises).filter((e: any) => e.done).length
    : 0;
  const totalCount = targets.length;

  return (
    <div className="bg-white rounded-3xl p-5 shadow-sm border-2 border-blue-100">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
          <Icon className="w-6 h-6 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-base font-semibold text-gray-900">
              {recommendation.title}
            </h4>
            {totalCount > 0 && (
              <span className={`text-xs font-bold px-2 py-1 rounded-full ${
                doneCount === totalCount
                  ? 'bg-green-100 text-green-700'
                  : 'bg-blue-50 text-blue-600'
              }`}>
                {doneCount}/{totalCount} 완료
              </span>
            )}
          </div>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
            {recommendation.content}
          </p>

          {/* 4개 운동 진행도 */}
          {targets.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100 space-y-2">
              <p className="text-xs font-medium text-gray-500 mb-3">운동 목표 및 진행도</p>
              {targets.map((t, i) => {
                const ep = progress?.exercises?.[t.exercise];
                const isDone = ep?.done ?? false;
                return (
                  <div key={i} className={`rounded-xl p-3 border ${isDone ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                          isDone ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'
                        }`}>
                          {isDone ? '✓' : i + 1}
                        </span>
                        <span className="text-sm font-medium text-gray-800">
                          {EXERCISE_LABELS[t.exercise]}
                        </span>
                        <span className="text-xs text-gray-500">
                          {t.sets}세트 × {t.reps}회
                        </span>
                      </div>
                      {isDone ? (
                        <div className="text-right">
                          <p className="text-xs text-green-600 font-medium">{ep!.totalReps}회 완료</p>
                          <p className="text-xs text-gray-400">자세 {ep!.postureScore.toFixed(1)}점</p>
                        </div>
                      ) : (
                        <button
                          onClick={() => startWorkout(t)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <PlayIcon className="w-3 h-3" />
                          시작
                        </button>
                      )}
                    </div>
                    {isDone && ep?.completedAt && (
                      <p className="text-xs text-gray-400 mt-1 ml-7">
                        {new Date(ep.completedAt).toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </p>
                    )}
                  </div>
                );
              })}

              {/* 전체 진행바 */}
              {totalCount > 0 && (
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>전체 진행도</span>
                    <span>{Math.round((doneCount / totalCount) * 100)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${(doneCount / totalCount) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          <p className="text-xs text-gray-400 mt-3">
            {new Date(recommendation.createdAt).toLocaleDateString('ko-KR')}
          </p>
        </div>
      </div>
    </div>
  );
}
