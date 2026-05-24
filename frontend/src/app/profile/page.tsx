'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';
import toast from 'react-hot-toast';

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [hasExisting, setHasExisting] = useState(false);

  // Body Profile fields
  const [heightCm, setHeightCm] = useState('');
  const [weightKg, setWeightKg] = useState('');
  const [bodyFatPercentage, setBodyFatPercentage] = useState('');

  const [errors, setErrors] = useState({
    heightCm: '',
    weightKg: '',
    bodyFatPercentage: '',
  });

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    // Load existing profile if available
    loadExistingProfile();
  }, [isAuthenticated, router]);

  const loadExistingProfile = async () => {
    try {
      const response = await apiClient.getLatestBodyProfile();
      if (response.data) {
        setHeightCm(response.data.heightCm?.toString() || '');
        setWeightKg(response.data.weightKg?.toString() || '');
        setBodyFatPercentage(response.data.bodyFatPercentage?.toString() || '');
        setHasExisting(true);
      }
    } catch (error: any) {
      // No existing profile is OK
      console.log('No existing profile');
    }
  };

  const validateForm = () => {
    const newErrors = {
      heightCm: '',
      weightKg: '',
      bodyFatPercentage: '',
    };

    const height = parseFloat(heightCm);
    const weight = parseFloat(weightKg);
    const bodyFat = parseFloat(bodyFatPercentage);

    if (!heightCm || isNaN(height) || height < 100 || height > 250) {
      newErrors.heightCm = '키는 100cm ~ 250cm 사이여야 합니다';
    }

    if (!weightKg || isNaN(weight) || weight < 30 || weight > 300) {
      newErrors.weightKg = '몸무게는 30kg ~ 300kg 사이여야 합니다';
    }

    if (bodyFatPercentage && (isNaN(bodyFat) || bodyFat < 3 || bodyFat > 60)) {
      newErrors.bodyFatPercentage = '체지방률은 3% ~ 60% 사이여야 합니다';
    }

    setErrors(newErrors);
    return !Object.values(newErrors).some((error) => error !== '');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      await apiClient.createBodyProfile({
        heightCm: parseInt(heightCm),
        weightKg: parseFloat(weightKg),
        bodyFatPercentage: bodyFatPercentage ? parseFloat(bodyFatPercentage) : undefined,
      });

      toast.success(hasExisting ? '신체 정보가 업데이트되었습니다!' : '신체 정보가 저장되었습니다!');
      router.push('/dashboard');
    } catch (error: any) {
      console.error('Failed to save body profile:', error);
      toast.error('저장에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">신체 정보 입력</h1>
          <p className="mt-2 text-gray-600">
            정확한 운동 추천을 위해 신체 정보를 입력해주세요
          </p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              label="키 (cm)"
              type="number"
              step="0.1"
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
              placeholder="예: 175"
              error={errors.heightCm}
              required
            />

            <Input
              label="몸무게 (kg)"
              type="number"
              step="0.1"
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
              placeholder="예: 70.5"
              error={errors.weightKg}
              required
            />

            <Input
              label="체지방률 (%, 선택사항)"
              type="number"
              step="0.1"
              value={bodyFatPercentage}
              onChange={(e) => setBodyFatPercentage(e.target.value)}
              placeholder="예: 18.5"
              error={errors.bodyFatPercentage}
              helperText="인바디 측정 결과가 있다면 입력해주세요"
            />

            <div className="flex gap-4">
              <Button
                type="submit"
                fullWidth
                disabled={loading}
              >
                {loading ? '저장 중...' : hasExisting ? '업데이트' : '저장'}
              </Button>

              <Button
                type="button"
                variant="secondary"
                onClick={handleSkip}
                disabled={loading}
              >
                나중에
              </Button>
            </div>
          </form>
        </Card>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p>신체 정보는 언제든지 수정할 수 있습니다</p>
        </div>
      </div>
    </div>
  );
}
