import { Card } from '@/components/ui/Card';

const EXERCISE_LABELS: Record<string, string> = {
  squat: '스쿼트',
  pushup: '푸시업',
  lunge: '런지',
  plank: '플랭크',
};

interface RepCounterProps {
  count: number;         // total repCount from server (or currentSetReps for non-plank)
  exercise: string;
  targetReps?: number | null;
  targetSets?: number | null;
  holdSeconds?: number;   // cumulative plank hold seconds
  currentSet?: number;    // 1-based
  restCountdown?: number; // 0 = not resting
  currentSetReps?: number; // reps in current set only (for display)
}

function formatTime(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
}

export function RepCounter({
  count,
  exercise,
  targetReps,
  targetSets,
  holdSeconds = 0,
  currentSet = 1,
  restCountdown = 0,
  currentSetReps,
}: RepCounterProps) {
  const label = EXERCISE_LABELS[exercise] || exercise;
  const isPlank = exercise === 'plank';
  const totalSets = targetSets ?? 1;

  // ── 휴식 중 화면 ──────────────────────────────────────────────────────────
  if (restCountdown > 0) {
    return (
      <Card>
        <div className="text-center">
          <p className="text-sm font-semibold text-orange-600 mb-1">휴식 중</p>
          <div className="text-6xl font-bold text-orange-500 mb-1 font-mono">
            {restCountdown}
          </div>
          <p className="text-sm text-gray-500">초 후 다음 세트 시작</p>
          <div className="mt-3 w-full bg-orange-100 rounded-full h-2">
            <div
              className="bg-orange-500 h-2 rounded-full transition-all duration-1000"
              style={{ width: `${(restCountdown / 10) * 100}%` }}
            />
          </div>
        </div>
      </Card>
    );
  }

  // ── 플랭크: 유지 시간 기반 ───────────────────────────────────────────────
  if (isPlank) {
    const targetSeconds = targetReps ?? null;
    const totalTargetSec = targetSeconds != null ? totalSets * targetSeconds : null;
    const currentSetHold = targetSeconds != null
      ? Math.max(0, holdSeconds - (currentSet - 1) * targetSeconds)
      : holdSeconds;
    const setProgress = targetSeconds ? Math.min((currentSetHold / targetSeconds) * 100, 100) : null;
    const setAchieved = targetSeconds != null && currentSetHold >= targetSeconds;

    return (
      <Card>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold text-gray-600">유지 시간</h3>
          {targetSets && targetSets > 1 && (
            <span className="text-xs font-bold px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
              세트 {Math.min(currentSet, totalSets)}/{totalSets}
            </span>
          )}
        </div>

        <div className="text-center mb-3">
          <div className="text-5xl font-bold text-blue-600 mb-1 font-mono">
            {formatTime(currentSetHold)}
          </div>
          {targetSeconds != null ? (
            <div className="text-sm text-gray-500">
              / {formatTime(targetSeconds)} 목표
              {totalTargetSec != null && (
                <span className="ml-1 text-xs text-gray-400">
                  (누적 {formatTime(holdSeconds)})
                </span>
              )}
            </div>
          ) : (
            <div className="text-sm text-gray-400">자유 플랭크</div>
          )}
        </div>

        {setProgress != null && (
          <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${setProgress}%` }}
            />
          </div>
        )}

        {setAchieved && (
          <div className="p-2 bg-green-50 border border-green-200 rounded-lg text-center">
            <p className="text-green-700 font-semibold text-sm">이 세트 달성!</p>
          </div>
        )}

        <div className="mt-2 text-xs text-gray-400 text-center">{label}</div>
      </Card>
    );
  }

  // ── 반복 운동: 횟수 기반 ───────────────────────────────────────────────────
  const displayCount = currentSetReps ?? count;
  const hasTarget = targetReps != null && targetReps > 0;
  const setProgress = hasTarget ? Math.min((displayCount / targetReps!) * 100, 100) : null;
  const setAchieved = hasTarget && displayCount >= targetReps!;

  return (
    <Card>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-600">반복 횟수</h3>
        {targetSets && targetSets > 1 && (
          <span className="text-xs font-bold px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
            세트 {Math.min(currentSet, totalSets)}/{totalSets}
          </span>
        )}
      </div>

      <div className="text-center mb-3">
        <div className="text-5xl font-bold text-blue-600 mb-1">{displayCount}</div>
        {hasTarget ? (
          <div className="text-sm text-gray-500">
            / {targetReps}회 목표
            <span className="ml-1 text-xs text-gray-400">
              (총 {count}회)
            </span>
          </div>
        ) : (
          <div className="text-sm text-gray-400">자유 운동</div>
        )}
      </div>

      {setProgress != null && (
        <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
          <div
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${setProgress}%` }}
          />
        </div>
      )}

      {setAchieved && (
        <div className="p-2 bg-green-50 border border-green-200 rounded-lg text-center">
          <p className="text-green-700 font-semibold text-sm">이 세트 달성!</p>
        </div>
      )}

      <div className="mt-2 text-xs text-gray-400 text-center">{label}</div>
    </Card>
  );
}
