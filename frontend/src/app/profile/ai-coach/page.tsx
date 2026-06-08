'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api-client';
import {
  ChevronLeftIcon,
  SparklesIcon,
  PlayIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { CheckCircleIcon as CheckCircleSolid } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';

// ── Types ──────────────────────────────────────────────────────────────────

interface TargetExercise {
  exercise: string;
  sets: number;
  reps: number; // seconds for plank
}

interface ExerciseProgress {
  done: boolean;
  completedAt: string | null;
  totalReps: number;
  holdSeconds?: number;
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
  content: string;
  createdAt: string;
  goal?: string;
  fitnessLevel?: string;
  targetExercises?: TargetExercise[];
}

// ── Constants ──────────────────────────────────────────────────────────────

const EXERCISE_LABELS: Record<string, string> = {
  squat: '스쿼트',
  pushup: '푸시업',
  lunge: '런지',
  plank: '플랭크',
};

const EXERCISE_ICONS: Record<string, string> = {
  squat: '🦵',
  pushup: '💪',
  lunge: '🏃',
  plank: '🧘',
};

const GOAL_LABELS: Record<string, string> = {
  weight_loss: '체중 감량',
  muscle_gain: '근육 증가',
  endurance: '지구력 향상',
  general_fitness: '전반적인 건강',
};

// ── Helpers ────────────────────────────────────────────────────────────────

function loadRecProgress(id: string): RecProgress | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(`gympt_rec_progress_${id}`);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function parseTargetExercises(raw: unknown): TargetExercise[] {
  if (!raw) return [];
  try {
    const arr = typeof raw === 'string' ? JSON.parse(raw) : raw;
    if (!Array.isArray(arr)) return [];
    return arr.filter(
      (t: any) => t && EXERCISE_LABELS[t.exercise] && t.sets > 0 && t.reps > 0,
    );
  } catch { return []; }
}

function formatTarget(exercise: string, sets: number, reps: number): string {
  if (exercise === 'plank') return `${sets}세트 × ${reps}초`;
  return `${sets}세트 × ${reps}회`;
}

function formatAchieved(exercise: string, ep: ExerciseProgress): string {
  if (exercise === 'plank') {
    const s = ep.holdSeconds ?? ep.totalReps;
    return `${s}초 유지`;
  }
  return `${ep.totalReps}회 완료`;
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function AICoachPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'current' | 'history'>('current');
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    goal: 'weight_loss',
    fitness_level: 'intermediate',
    days_per_week: 3,
    injuries_or_limitations: '',
  });

  useEffect(() => {
    if (user) loadRecommendations();
  }, [user?.userId]);

  const loadRecommendations = async () => {
    try {
      setLoadingHistory(true);
      const response = await apiClient.getWorkoutRecommendations(20) as any;
      const items = Array.isArray(response) ? response : response?.data ?? [];
      if (items.length > 0) {
        setRecommendations(
          items.map((rec: any) => ({
            id: rec.id,
            content: rec.recommendation,
            createdAt: rec.createdAt,
            goal: rec.goal,
            fitnessLevel: rec.fitnessLevel,
            targetExercises: parseTargetExercises(rec.targetExercises),
          })),
        );
      }
    } catch (e) {
      console.error('Failed to load recommendations:', e);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleGetNewRecommendation = async () => {
    if (!user?.userId) { toast.error('사용자 정보를 찾을 수 없습니다'); return; }
    setLoading(true);
    try {
      let bodyProfile: any = null;
      try { bodyProfile = await apiClient.getLatestBodyProfile() as any; } catch {}

      await apiClient.getWorkoutRecommendation({
        user_id: user.userId,
        goal: formData.goal,
        fitness_level: formData.fitness_level,
        days_per_week: formData.days_per_week,
        equipment_available: [],
        injuries_or_limitations: formData.injuries_or_limitations || undefined,
        ...(bodyProfile && {
          height: bodyProfile.height,
          weight: bodyProfile.weight,
          body_fat: bodyProfile.bodyFat,
          muscle_mass: bodyProfile.muscleMass,
        }),
      });

      toast.success('새로운 추천을 받았습니다!');
      await loadRecommendations();
      setShowForm(false);
      setActiveTab('current');
    } catch {
      toast.error('추천을 받는데 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const latest = recommendations[0] ?? null;
  const history = recommendations.slice(1);

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto pb-20">

          {/* ── Header ── */}
          <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center sticky top-0 z-10">
            <button
              onClick={() => router.back()}
              className="p-2 -ml-2 hover:bg-gray-100 rounded-full"
            >
              <ChevronLeftIcon className="w-6 h-6 text-gray-700" />
            </button>
            <h1 className="flex-1 text-lg font-semibold text-gray-900 text-center mr-10">
              AI 코치
            </h1>
          </div>

          {/* ── Tab Bar ── */}
          <div className="bg-white border-b border-gray-200 sticky top-[57px] z-10">
            <div className="flex">
              {(['current', 'history'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`flex-1 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab === 'current' ? '현재 추천' : '추천 이력'}
                </button>
              ))}
            </div>
          </div>

          {/* ── Tab Content ── */}
          <div className="px-4 py-5 space-y-4">
            {activeTab === 'current' ? (
              <CurrentTab
                latest={latest}
                loadingHistory={loadingHistory}
                loading={loading}
                showForm={showForm}
                setShowForm={setShowForm}
                formData={formData}
                setFormData={setFormData}
                handleGetNewRecommendation={handleGetNewRecommendation}
              />
            ) : (
              <HistoryTab history={history} loadingHistory={loadingHistory} />
            )}
          </div>

        </div>
      </div>
    </ProtectedRoute>
  );
}

// ── Current Tab ────────────────────────────────────────────────────────────

interface CurrentTabProps {
  latest: Recommendation | null;
  loadingHistory: boolean;
  loading: boolean;
  showForm: boolean;
  setShowForm: (v: boolean) => void;
  formData: any;
  setFormData: (v: any) => void;
  handleGetNewRecommendation: () => void;
}

function CurrentTab({
  latest, loadingHistory, loading, showForm, setShowForm, formData, setFormData, handleGetNewRecommendation,
}: CurrentTabProps) {
  return (
    <>
      {/* Hero */}
      <div className="bg-gradient-to-br from-purple-500 to-blue-600 rounded-3xl p-5 shadow-lg text-white">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
            <SparklesIcon className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold">AI 맞춤 운동 코치</h2>
            <p className="text-xs opacity-80">체성분·목표 기반 개인 맞춤형 프로그램</p>
          </div>
        </div>
      </div>

      {/* New recommendation button / form */}
      {!showForm ? (
        <button
          onClick={() => setShowForm(true)}
          className="w-full bg-blue-600 text-white rounded-2xl p-4 shadow-sm hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
        >
          <SparklesIcon className="w-5 h-5" />
          <span className="font-medium">새 추천 받기</span>
        </button>
      ) : (
        <RecommendationForm
          loading={loading}
          formData={formData}
          setFormData={setFormData}
          onCancel={() => setShowForm(false)}
          onSubmit={handleGetNewRecommendation}
        />
      )}

      {/* Latest recommendation */}
      {loadingHistory ? (
        <div className="bg-white rounded-3xl p-10 text-center shadow-sm">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3" />
          <p className="text-sm text-gray-500">불러오는 중...</p>
        </div>
      ) : latest ? (
        <LatestRecommendationCard recommendation={latest} />
      ) : !showForm ? (
        <div className="bg-white rounded-3xl p-12 text-center shadow-sm">
          <SparklesIcon className="w-14 h-14 text-gray-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-gray-900 mb-1">추천 내역이 없습니다</h3>
          <p className="text-sm text-gray-500">위 버튼을 눌러 첫 AI 추천을 받아보세요</p>
        </div>
      ) : null}
    </>
  );
}

// ── Latest Recommendation Card ──────────────────────────────────────────────

function LatestRecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const router = useRouter();
  const [progress, setProgress] = useState<RecProgress | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (recommendation.id) setProgress(loadRecProgress(recommendation.id));
  }, [recommendation.id]);

  const targets = recommendation.targetExercises ?? [];
  const doneCount = progress
    ? Object.values(progress.exercises).filter((e: any) => e.done).length
    : 0;

  const startWorkout = (t: TargetExercise) => {
    const params = new URLSearchParams({
      exercise: t.exercise,
      sets: String(t.sets),
      reps: String(t.reps),
    });
    if (recommendation.id) params.set('recommendationId', recommendation.id);
    router.push(`/workout?${params.toString()}`);
  };

  const allDone = targets.length > 0 && doneCount === targets.length;

  return (
    <div className="bg-white rounded-3xl shadow-sm overflow-hidden border border-gray-100">
      {/* Card header */}
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-400">
            {new Date(recommendation.createdAt).toLocaleDateString('ko-KR', {
              year: 'numeric', month: 'long', day: 'numeric',
            })}
          </span>
          {targets.length > 0 && (
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
              allDone ? 'bg-green-100 text-green-700' : 'bg-blue-50 text-blue-600'
            }`}>
              {allDone ? '✓ 완료' : `${doneCount}/${targets.length} 완료`}
            </span>
          )}
        </div>
        <h3 className="text-base font-bold text-gray-900">오늘의 맞춤 운동 프로그램</h3>
        {recommendation.goal && (
          <p className="text-xs text-gray-500 mt-0.5">
            목표: {GOAL_LABELS[recommendation.goal] ?? recommendation.goal}
          </p>
        )}
      </div>

      {/* Overall progress bar */}
      {targets.length > 0 && (
        <div className="px-5 pb-3">
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span>전체 진행도</span>
            <span>{Math.round((doneCount / targets.length) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all"
              style={{ width: `${(doneCount / targets.length) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Exercise list */}
      {targets.length > 0 && (
        <div className="px-5 pb-4 space-y-2">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            운동 목록
          </p>
          {targets.map((t, i) => {
            const ep = progress?.exercises?.[t.exercise];
            const isDone = ep?.done ?? false;
            return (
              <div
                key={i}
                className={`rounded-2xl p-4 border-2 transition-colors ${
                  isDone
                    ? 'bg-green-50 border-green-200'
                    : 'bg-gray-50 border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{EXERCISE_ICONS[t.exercise] ?? '🏋️'}</span>
                    <div>
                      <p className="text-sm font-semibold text-gray-900">
                        {EXERCISE_LABELS[t.exercise]}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatTarget(t.exercise, t.sets, t.reps)}
                      </p>
                    </div>
                  </div>

                  {isDone ? (
                    <div className="text-right">
                      <CheckCircleSolid className="w-5 h-5 text-green-500 ml-auto mb-1" />
                      <p className="text-xs text-green-700 font-medium">
                        {formatAchieved(t.exercise, ep!)}
                      </p>
                      <p className="text-xs text-gray-400">자세 {ep!.postureScore.toFixed(0)}점</p>
                    </div>
                  ) : (
                    <button
                      onClick={() => startWorkout(t)}
                      className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-xl hover:bg-blue-700 transition-colors"
                    >
                      <PlayIcon className="w-4 h-4" />
                      시작
                    </button>
                  )}
                </div>

                {isDone && ep?.completedAt && (
                  <p className="text-xs text-gray-400 mt-2 ml-11">
                    완료: {new Date(ep.completedAt).toLocaleString('ko-KR', {
                      month: 'short', day: 'numeric',
                      hour: '2-digit', minute: '2-digit',
                    })}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Full recommendation text (collapsible) */}
      <div className="border-t border-gray-100">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-5 py-3 text-sm text-gray-500 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <span>AI 추천 전체 내용</span>
          <span className="text-gray-400">{expanded ? '▲' : '▼'}</span>
        </button>
        {expanded && (
          <div className="px-5 pb-5">
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
              {recommendation.content}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── History Tab ────────────────────────────────────────────────────────────

function HistoryTab({ history, loadingHistory }: { history: Recommendation[]; loadingHistory: boolean }) {
  const router = useRouter();

  if (loadingHistory) {
    return (
      <div className="bg-white rounded-3xl p-10 text-center shadow-sm">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3" />
        <p className="text-sm text-gray-500">불러오는 중...</p>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="bg-white rounded-3xl p-12 text-center shadow-sm">
        <ClockIcon className="w-14 h-14 text-gray-300 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-gray-900 mb-1">이전 추천이 없습니다</h3>
        <p className="text-sm text-gray-500">추천을 받을수록 이력이 쌓입니다</p>
      </div>
    );
  }

  // Group by date
  const grouped = history.reduce<Record<string, Recommendation[]>>((acc, rec) => {
    const date = new Date(rec.createdAt).toLocaleDateString('ko-KR', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
    if (!acc[date]) acc[date] = [];
    acc[date].push(rec);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {Object.entries(grouped).map(([date, recs]) => (
        <div key={date}>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2 px-1">
            {date}
          </p>
          <div className="space-y-3">
            {recs.map((rec, i) => (
              <HistoryCard key={rec.id ?? i} recommendation={rec} router={router} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function HistoryCard({ recommendation, router }: { recommendation: Recommendation; router: any }) {
  const [expanded, setExpanded] = useState(false);
  const [progress, setProgress] = useState<RecProgress | null>(null);

  useEffect(() => {
    if (recommendation.id) setProgress(loadRecProgress(recommendation.id));
  }, [recommendation.id]);

  const targets = recommendation.targetExercises ?? [];
  const doneCount = progress
    ? Object.values(progress.exercises).filter((e: any) => e.done).length
    : 0;

  const startWorkout = (t: TargetExercise) => {
    const params = new URLSearchParams({
      exercise: t.exercise,
      sets: String(t.sets),
      reps: String(t.reps),
    });
    if (recommendation.id) params.set('recommendationId', recommendation.id);
    router.push(`/workout?${params.toString()}`);
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <SparklesIcon className="w-5 h-5 text-purple-500 flex-shrink-0" />
          <div className="text-left">
            <p className="text-sm font-semibold text-gray-900">맞춤 운동 프로그램</p>
            {recommendation.goal && (
              <p className="text-xs text-gray-400">
                {GOAL_LABELS[recommendation.goal] ?? recommendation.goal}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {targets.length > 0 && (
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              doneCount === targets.length && targets.length > 0
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-500'
            }`}>
              {doneCount}/{targets.length}
            </span>
          )}
          <span className="text-gray-400 text-sm">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-2 border-t border-gray-100 pt-3">
          {targets.length > 0 ? (
            targets.map((t, i) => {
              const ep = progress?.exercises?.[t.exercise];
              const isDone = ep?.done ?? false;
              return (
                <div key={i} className={`rounded-xl p-3 flex items-center justify-between ${
                  isDone ? 'bg-green-50' : 'bg-gray-50'
                }`}>
                  <div className="flex items-center gap-2">
                    <span>{EXERCISE_ICONS[t.exercise] ?? '🏋️'}</span>
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {EXERCISE_LABELS[t.exercise]}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatTarget(t.exercise, t.sets, t.reps)}
                      </p>
                    </div>
                  </div>
                  {isDone ? (
                    <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  ) : (
                    <button
                      onClick={() => startWorkout(t)}
                      className="text-xs px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      시작
                    </button>
                  )}
                </div>
              );
            })
          ) : (
            <p className="text-sm text-gray-600 whitespace-pre-wrap line-clamp-4">
              {recommendation.content}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ── Recommendation Form ────────────────────────────────────────────────────

function RecommendationForm({
  loading, formData, setFormData, onCancel, onSubmit,
}: {
  loading: boolean;
  formData: any;
  setFormData: (v: any) => void;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  return (
    <div className="bg-white rounded-3xl p-5 shadow-sm space-y-4">
      <h3 className="text-base font-semibold text-gray-900">운동 목표 설정</h3>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">운동 목표</label>
        <select
          value={formData.goal}
          onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
        >
          <option value="weight_loss">체중 감량</option>
          <option value="muscle_gain">근육 증가</option>
          <option value="endurance">지구력 향상</option>
          <option value="general_fitness">전반적인 건강</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">운동 수준</label>
        <select
          value={formData.fitness_level}
          onChange={(e) => setFormData({ ...formData, fitness_level: e.target.value })}
          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
        >
          <option value="beginner">초급</option>
          <option value="intermediate">중급</option>
          <option value="advanced">고급</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">주간 운동 횟수</label>
        <input
          type="number" min="1" max="7"
          value={formData.days_per_week}
          onChange={(e) => setFormData({ ...formData, days_per_week: parseInt(e.target.value) || 3 })}
          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">부상 또는 제한사항</label>
        <textarea
          value={formData.injuries_or_limitations}
          onChange={(e) => setFormData({ ...formData, injuries_or_limitations: e.target.value })}
          placeholder="예: 무릎 통증, 허리 디스크 등 (없으면 비워두세요)"
          rows={2}
          className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
        />
      </div>

      <div className="flex gap-2 pt-1">
        <button
          onClick={onCancel}
          className="flex-1 px-4 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors text-sm"
        >
          취소
        </button>
        <button
          onClick={onSubmit}
          disabled={loading}
          className="flex-1 px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 text-sm"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
              AI 분석 중...
            </>
          ) : (
            <>
              <SparklesIcon className="w-4 h-4" />
              추천 받기
            </>
          )}
        </button>
      </div>
    </div>
  );
}
