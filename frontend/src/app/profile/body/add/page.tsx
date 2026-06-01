'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { Button } from '@/components/ui/Button';
import { ChevronLeftIcon } from '@heroicons/react/24/outline';
import { apiClient } from '@/lib/api-client';
import toast from 'react-hot-toast';

export default function AddBodyDataPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    height: '',
    weight: '',
    bodyFat: '',
    muscleMass: '',
    measurementDate: new Date().toISOString().split('T')[0],
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.height || !formData.weight) {
      toast.error('키와 체중은 필수 입력 항목입니다');
      return;
    }

    setLoading(true);
    const data: any = {
      height: parseFloat(formData.height),
      weight: parseFloat(formData.weight),
      measurementDate: formData.measurementDate,
    };
    if (formData.bodyFat) data.bodyFat = parseFloat(formData.bodyFat);
    if (formData.muscleMass) data.muscleMass = parseFloat(formData.muscleMass);

    try {
      await apiClient.createBodyProfile(data);
      toast.success('인바디 정보가 저장되었습니다');
      router.push('/profile/body');
    } catch {
      // API unavailable → save to localStorage for demo
      try {
        const entry = { ...data, id: `local-${Date.now()}` };
        const existing: any[] = JSON.parse(localStorage.getItem('gympt_body_history') || '[]');
        existing.unshift(entry);
        localStorage.setItem('gympt_body_history', JSON.stringify(existing));
        localStorage.setItem('gympt_body_latest', JSON.stringify(entry));
        toast.success('인바디 정보가 저장되었습니다');
        router.push('/profile/body');
      } catch {
        toast.error('저장에 실패했습니다');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center">
            <button
              onClick={() => router.back()}
              className="p-2 -ml-2 hover:bg-gray-100 rounded-full"
            >
              <ChevronLeftIcon className="w-6 h-6 text-gray-700" />
            </button>
            <h1 className="flex-1 text-lg font-semibold text-gray-900 text-center mr-10">
              인바디 측정 추가
            </h1>
          </div>

          {/* Form */}
          <div className="px-4 py-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="bg-white rounded-3xl p-6 shadow-sm space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    측정 날짜 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={formData.measurementDate}
                    onChange={(e) => setFormData({ ...formData, measurementDate: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    키 (cm) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="50"
                    max="300"
                    value={formData.height}
                    onChange={(e) => setFormData({ ...formData, height: e.target.value })}
                    placeholder="예: 175.0"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    체중 (kg) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="20"
                    max="500"
                    value={formData.weight}
                    onChange={(e) => setFormData({ ...formData, weight: e.target.value })}
                    placeholder="예: 70.5"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    체지방률 (%) <span className="text-gray-400 text-xs">선택</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={formData.bodyFat}
                    onChange={(e) => setFormData({ ...formData, bodyFat: e.target.value })}
                    placeholder="예: 15.2"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    골격근량 (kg) <span className="text-gray-400 text-xs">선택</span>
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={formData.muscleMass}
                    onChange={(e) => setFormData({ ...formData, muscleMass: e.target.value })}
                    placeholder="예: 32.4"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-2xl disabled:opacity-50"
              >
                {loading ? '저장 중...' : '저장하기'}
              </Button>
            </form>

            <div className="mt-6 bg-blue-50 rounded-2xl p-4">
              <p className="text-sm text-blue-800 leading-relaxed">
                <span className="font-semibold">참고:</span> 인바디 측정 데이터를 정기적으로 입력하면
                AI 코치가 더 정확한 운동 및 영양 추천을 제공합니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
