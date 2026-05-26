'use client';

import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline';

export interface FeedbackData {
  form_score: number;
  is_valid: boolean;
  feedback: string[];
  rep_count?: number;
}

export interface FeedbackPanelProps {
  feedback: FeedbackData | null;
  className?: string;
}

export function FeedbackPanel({ feedback, className = '' }: FeedbackPanelProps) {
  if (!feedback) {
    return (
      <div className={`bg-gray-800 rounded-2xl p-6 ${className}`}>
        <div className="text-center text-gray-400">
          <p className="text-sm">자세 분석 대기 중...</p>
        </div>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 80) return <CheckCircleIcon className="w-8 h-8 text-green-500" />;
    if (score >= 60) return <ExclamationTriangleIcon className="w-8 h-8 text-yellow-500" />;
    return <XCircleIcon className="w-8 h-8 text-red-500" />;
  };

  return (
    <div className={`bg-gray-800 rounded-2xl p-6 ${className}`}>
      {/* Score Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          {getScoreIcon(feedback.form_score)}
          <div>
            <h3 className="text-white font-semibold text-lg">자세 점수</h3>
            <p className={`text-3xl font-bold ${getScoreColor(feedback.form_score)}`}>
              {feedback.form_score}
              <span className="text-sm text-gray-400 ml-1">/ 100</span>
            </p>
          </div>
        </div>
        {feedback.rep_count !== undefined && (
          <div className="text-right">
            <p className="text-gray-400 text-sm">반복 횟수</p>
            <p className="text-white text-2xl font-bold">{feedback.rep_count}</p>
          </div>
        )}
      </div>

      {/* Feedback Messages */}
      <div className="space-y-3">
        <h4 className="text-white font-medium text-sm">피드백</h4>
        {feedback.feedback && feedback.feedback.length > 0 ? (
          <ul className="space-y-2">
            {feedback.feedback.map((msg, idx) => (
              <li
                key={idx}
                className="flex items-start space-x-2 text-sm"
              >
                <span className="text-blue-400 mt-0.5">•</span>
                <span className="text-gray-300 flex-1">{msg}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-400 text-sm">자세가 좋습니다!</p>
        )}
      </div>

      {/* Status Badge */}
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
          feedback.is_valid
            ? 'bg-green-900/30 text-green-400 border border-green-500/30'
            : 'bg-red-900/30 text-red-400 border border-red-500/30'
        }`}>
          {feedback.is_valid ? '✓ 올바른 자세' : '✗ 자세 교정 필요'}
        </div>
      </div>
    </div>
  );
}
