'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import toast from 'react-hot-toast';

export default function GoalsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);

  const [goalType, setGoalType] = useState('weight_loss');
  const [targetValue, setTargetValue] = useState('');
  const [targetDate, setTargetDate] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    // Load existing goal if available
    loadExistingGoal();
  }, [isAuthenticated, router]);

  const loadExistingGoal = async () => {
    try {
      const response = await apiClient.getLatestGoal() as any;
      if (response) {
        setGoalType(response.goalType || 'weight_loss');
        setTargetValue(response.targetValue?.toString() || '');
        setTargetDate(response.targetDate || '');
      }
    } catch (error: any) {
      console.log('No existing goal');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!targetValue) {
      toast.error('목표 값을 입력해주세요');
      return;
    }

    setLoading(true);

    try {
      await apiClient.createGoal({
        goalType,
        targetValue: parseFloat(targetValue),
        targetDate: targetDate || null,
      });

      toast.success('운동 목표가 설정되었습니다!');
      router.push('/dashboard');
    } catch (error: any) {
      console.error('Failed to save goal:', error);
      toast.error('저장에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const goalTypes = [
    { value: 'weight_loss', label: '체중 감량', unit: 'kg' },
    { value: 'muscle_gain', label: '근육 증가', unit: 'kg' },
    { value: 'endurance', label: '지구력 향상', unit: '분' },
    { value: 'strength', label: '근력 향상', unit: 'kg' },
    { value: 'flexibility', label: '유연성 향상', unit: '점' },
  ];

  const selectedGoalType = goalTypes.find(g => g.value === goalType);

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">운동 목표 설정</h1>
          <p className="mt-2 text-gray-600">
            달성하고 싶은 목표를 설정해보세요
          </p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                목표 유형
              </label>
              <div className="grid grid-cols-2 gap-3">
                {goalTypes.map((type) => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => setGoalType(type.value)}
                    className={`p-4 rounded-lg border-2 text-left transition-colors ${
                      goalType === type.value
                        ? 'border-blue-600 bg-blue-50 text-blue-900'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-semibold">{type.label}</div>
                    <div className="text-sm text-gray-600 mt-1">단위: {type.unit}</div>
                  </button>
                ))}
              </div>
            </div>

            <Input
              label={`목표 값 (${selectedGoalType?.unit})`}
              type="number"
              step="0.1"
              value={targetValue}
              onChange={(e) => setTargetValue(e.target.value)}
              placeholder={
                goalType === 'weight_loss'
                  ? '예: -5 (5kg 감량)'
                  : goalType === 'endurance'
                  ? '예: 30 (30분 러닝)'
                  : '예: 5'
              }
              required
            />

            <Input
              label="목표 달성 날짜 (선택사항)"
              type="date"
              value={targetDate}
              onChange={(e) => setTargetDate(e.target.value)}
              helperText="목표를 달성하고 싶은 날짜를 선택하세요"
            />

            <div className="flex gap-4">
              <Button
                type="submit"
                fullWidth
                disabled={loading}
              >
                {loading ? '저장 중...' : '목표 설정'}
              </Button>

              <Button
                type="button"
                variant="secondary"
                onClick={() => router.push('/dashboard')}
                disabled={loading}
              >
                나중에
              </Button>
            </div>
          </form>
        </Card>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p>목표는 언제든지 수정할 수 있습니다</p>
        </div>
      </div>
    </div>
  );
}
