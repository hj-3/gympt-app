import { Card } from '@/components/ui/Card';

interface PostureAnalysis {
  score: number;
  feedback: string[];
  landmarks: any[];
  timestamp: string;
}

interface PostureFeedbackProps {
  analysis: PostureAnalysis | null;
}

export function PostureFeedback({ analysis }: PostureFeedbackProps) {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 6) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">Posture Feedback</h3>

      {!analysis ? (
        <div className="text-center py-8 text-gray-500">
          <p>Start your workout to see real-time feedback</p>
        </div>
      ) : (
        <>
          <div className={`mb-4 p-4 rounded-lg border-2 ${getScoreColor(analysis.score)}`}>
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">{analysis.score.toFixed(1)}</div>
              <div className="text-sm">Posture Score</div>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="font-semibold text-sm text-gray-700">Corrections:</h4>
            {analysis.feedback.length === 0 ? (
              <p className="text-sm text-green-600">Perfect form! Keep it up!</p>
            ) : (
              <ul className="space-y-2">
                {analysis.feedback.map((item, index) => (
                  <li
                    key={index}
                    className="text-sm p-2 bg-blue-50 border border-blue-200 rounded"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </Card>
  );
}
