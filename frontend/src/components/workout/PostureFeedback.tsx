import { Card } from '@/components/ui/Card';

interface PostureAnalysis {
  formScore: number;
  isValid: boolean;
  feedback: string[];
  angles: Record<string, number>;
  timestamp: string;
  repCount: number;
}

interface PostureFeedbackProps {
  analysis: PostureAnalysis | null;
}

export function PostureFeedback({ analysis }: PostureFeedbackProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">실시간 자세 피드백</h3>

      {!analysis ? (
        <div className="text-center py-8 text-gray-500">
          <p>운동을 시작하면 실시간 피드백이 표시됩니다</p>
        </div>
      ) : (
        <>
          <div className={`mb-4 p-4 rounded-lg border-2 ${getScoreColor(analysis.formScore)}`}>
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">{analysis.formScore.toFixed(1)}</div>
              <div className="text-sm">Form Score (out of 100)</div>
            </div>
            <div className="mt-2 text-center">
              {analysis.isValid ? (
                <span className="text-green-600 text-sm font-semibold">✓ 올바른 자세</span>
              ) : (
                <span className="text-orange-600 text-sm font-semibold">⚠ 자세 교정 필요</span>
              )}
            </div>
          </div>

          {/* Angles Display */}
          {Object.keys(analysis.angles).length > 0 && (
            <div className="mb-4">
              <h4 className="font-semibold text-sm text-gray-700 mb-2">관절 각도:</h4>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(analysis.angles).map(([key, value]) => (
                  <div key={key} className="text-xs p-2 bg-gray-100 rounded">
                    <span className="font-medium">{key}:</span>{' '}
                    <span className="text-blue-600">{value.toFixed(1)}°</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Feedback Messages */}
          <div className="space-y-2">
            <h4 className="font-semibold text-sm text-gray-700">피드백:</h4>
            {analysis.feedback.length === 0 ? (
              <p className="text-sm text-green-600">✓ 완벽한 자세입니다!</p>
            ) : (
              <ul className="space-y-2">
                {analysis.feedback.map((item, index) => (
                  <li
                    key={index}
                    className={`text-sm p-2 rounded border ${
                      item.startsWith('✓') || item.includes('good') || item.includes('Good')
                        ? 'bg-green-50 border-green-200 text-green-800'
                        : 'bg-orange-50 border-orange-200 text-orange-800'
                    }`}
                  >
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Timestamp */}
          <div className="mt-4 text-xs text-gray-400 text-right">
            마지막 업데이트: {new Date(analysis.timestamp).toLocaleTimeString('ko-KR')}
          </div>
        </>
      )}
    </Card>
  );
}
