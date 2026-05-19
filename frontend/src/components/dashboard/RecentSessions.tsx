import { Card } from '@/components/ui/Card';
import { format } from 'date-fns';

interface Session {
  sessionId: string;
  startTime: string;
  duration: number;
  exerciseCount: number;
  avgScore: number;
}

interface RecentSessionsProps {
  sessions: Session[];
}

export function RecentSessions({ sessions }: RecentSessionsProps) {
  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Recent Sessions</h3>

      {sessions.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No recent sessions</p>
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <div
              key={session.sessionId}
              className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition"
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-sm text-gray-600">
                  {format(new Date(session.startTime), 'MMM dd, yyyy')}
                </span>
                <span className="text-sm font-semibold text-blue-600">
                  {session.avgScore.toFixed(1)}/10
                </span>
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>{session.exerciseCount} exercises</span>
                <span>{session.duration} min</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
