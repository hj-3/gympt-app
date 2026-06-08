import { Card } from '@/components/ui/Card';

const EXERCISE_LABELS: Record<string, string> = {
  squat: '스쿼트',
  pushup: '푸시업',
  lunge: '런지',
  plank: '플랭크',
};

interface RepCounterProps {
  count: number;
  exercise: string;
  targetReps?: number | null;
  targetSets?: number | null;
  holdSeconds?: number;
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
}

export function RepCounter({ count, exercise, targetReps, targetSets, holdSeconds = 0 }: RepCounterProps) {
  const label = EXERCISE_LABELS[exercise] || exercise;
  const isPlank = exercise === 'plank';

  // ── 플랭크: 유지 시간 기반 ───────────────────────────────────────────
  if (isPlank) {
    // targetReps = 목표 초(초 단위), targetSets = 세트 수
    const targetSeconds = targetReps != null && targetReps > 0 ? targetReps : null;
    const totalTargetSec = targetSeconds != null ? (targetSets ?? 1) * targetSeconds : null;
    const progress = totalTargetSec ? Math.min((holdSeconds / totalTargetSec) * 100, 100) : null;
    const achieved = totalTargetSec != null && holdSeconds >= totalTargetSec;

    return (
      <Card>
        <h3 className="text-base font-semibold mb-3 text-gray-700">유지 시간</h3>

        <div className="text-center mb-4">
          <div className="text-6xl font-bold text-blue-600 mb-1 font-mono">
            {formatTime(holdSeconds)}
          </div>
          {totalTargetSec != null ? (
            <div className="text-sm text-gray-500">
              / {formatTime(totalTargetSec)} 목표
              {targetSets && targetSets > 1 && (
                <span className="ml-1 text-gray-400">
                  ({targetSets}세트 × {targetSeconds}초)
                </span>
              )}
            </div>
          ) : (
            <div className="text-sm text-gray-400">자유 플랭크 모드</div>
          )}
        </div>

        {progress != null && (
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden mb-2">
            <div
              className="bg-blue-600 h-full transition-all duration-300 ease-out rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {achieved && (
          <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-lg text-center">
            <p className="text-green-700 font-semibold text-sm">목표 달성!</p>
          </div>
        )}

        <div className="mt-3 text-xs text-gray-400 text-center">{label} — 자세 유지 시간</div>
      </Card>
    );
  }

  // ── 반복 운동: 횟수 기반 ───────────────────────────────────────────────
  const hasTarget = targetReps != null && targetReps > 0;
  const totalTarget = hasTarget ? (targetSets ?? 1) * targetReps! : null;
  const progress = totalTarget ? Math.min((count / totalTarget) * 100, 100) : null;

  return (
    <Card>
      <h3 className="text-base font-semibold mb-3 text-gray-700">반복 횟수</h3>

      <div className="text-center mb-4">
        <div className="text-6xl font-bold text-blue-600 mb-1">{count}</div>
        {hasTarget ? (
          <div className="text-sm text-gray-500">
            / {totalTarget}회 목표
            {targetSets && targetSets > 1 && (
              <span className="ml-1 text-gray-400">({targetSets}세트 × {targetReps}회)</span>
            )}
          </div>
        ) : (
          <div className="text-sm text-gray-400">자유 운동 모드</div>
        )}
      </div>

      {progress != null && (
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden mb-2">
          <div
            className="bg-blue-600 h-full transition-all duration-300 ease-out rounded-full"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {progress != null && totalTarget != null && count >= totalTarget && (
        <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-lg text-center">
          <p className="text-green-700 font-semibold text-sm">목표 달성!</p>
        </div>
      )}

      <div className="mt-3 text-xs text-gray-400 text-center">{label}</div>
    </Card>
  );
}
