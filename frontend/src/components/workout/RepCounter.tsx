import { Card } from '@/components/ui/Card';

interface RepCounterProps {
  count: number;
  exercise: string;
  targetReps?: number;
}

export function RepCounter({ count, exercise, targetReps = 12 }: RepCounterProps) {
  const progress = (count / targetReps) * 100;

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Repetitions</h3>

      <div className="text-center mb-4">
        <div className="text-6xl font-bold text-blue-600 mb-2">{count}</div>
        <div className="text-sm text-gray-600">
          of {targetReps} reps
        </div>
      </div>

      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className="bg-blue-600 h-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>

      {count >= targetReps && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-center">
          <p className="text-green-700 font-semibold">Target reached!</p>
        </div>
      )}

      <div className="mt-4 text-sm text-gray-600 text-center capitalize">
        Current: {exercise.replace(/-/g, ' ')}
      </div>
    </Card>
  );
}
