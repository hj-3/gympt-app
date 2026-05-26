'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api-client';
import {
  ExclamationTriangleIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function DeleteAccountPage() {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handleDeleteAccount = async () => {
    if (confirmText !== '회원탈퇴') {
      toast.error('확인 문구를 정확히 입력해주세요');
      return;
    }

    setIsDeleting(true);

    try {
      await apiClient.deleteCurrentAccount();
      toast.success('회원탈퇴가 완료되었습니다');

      // Sign out from Cognito
      await signOut();

      // Redirect to home
      setTimeout(() => {
        router.push('/');
      }, 1500);
    } catch (error: any) {
      console.error('Failed to delete account:', error);
      toast.error('회원탈퇴에 실패했습니다. 잠시 후 다시 시도해주세요');
      setIsDeleting(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto px-4 py-6">
          {/* Header */}
          <div className="flex items-center mb-8">
            <button
              onClick={() => router.back()}
              className="mr-4 p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="w-6 h-6 text-gray-900" />
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              회원탈퇴
            </h1>
          </div>

          {/* Warning Card */}
          <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-6 mb-6">
            <div className="flex items-start space-x-3">
              <ExclamationTriangleIcon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h2 className="text-lg font-semibold text-red-900 mb-2">
                  회원탈퇴 전 확인해주세요
                </h2>
                <ul className="space-y-2 text-sm text-red-800">
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>모든 운동 기록과 데이터가 삭제됩니다</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>AI 코치 추천 히스토리가 삭제됩니다</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>인바디 정보 및 신체 데이터가 삭제됩니다</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>삭제된 데이터는 복구할 수 없습니다</span>
                  </li>
                  <li className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>탈퇴 후 동일한 계정으로 재가입이 불가능할 수 있습니다</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* User Info */}
          <div className="bg-white rounded-2xl p-6 mb-6 shadow-sm">
            <h3 className="text-sm font-medium text-gray-500 mb-3">
              탈퇴할 계정
            </h3>
            <div className="space-y-2">
              <p className="text-base text-gray-900">
                <span className="font-medium">이름:</span> {user?.attributes?.name || '사용자'}
              </p>
              <p className="text-base text-gray-900">
                <span className="font-medium">이메일:</span> {user?.attributes?.email || '-'}
              </p>
            </div>
          </div>

          {!showConfirmation ? (
            <button
              onClick={() => setShowConfirmation(true)}
              className="w-full bg-gray-900 text-white rounded-2xl py-4 font-semibold hover:bg-gray-800 transition-colors"
            >
              탈퇴 진행하기
            </button>
          ) : (
            <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  정말로 탈퇴하시겠습니까?
                </label>
                <p className="text-sm text-gray-600 mb-4">
                  아래에 <span className="font-semibold text-red-600">&quot;회원탈퇴&quot;</span>를 입력해주세요
                </p>
                <input
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  placeholder="회원탈퇴"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  disabled={isDeleting}
                />
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setShowConfirmation(false);
                    setConfirmText('');
                  }}
                  className="flex-1 bg-gray-200 text-gray-700 rounded-xl py-3 font-medium hover:bg-gray-300 transition-colors"
                  disabled={isDeleting}
                >
                  취소
                </button>
                <button
                  onClick={handleDeleteAccount}
                  disabled={confirmText !== '회원탈퇴' || isDeleting}
                  className="flex-1 bg-red-600 text-white rounded-xl py-3 font-medium hover:bg-red-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {isDeleting ? '처리 중...' : '탈퇴하기'}
                </button>
              </div>
            </div>
          )}

          {/* Back Button */}
          {!showConfirmation && (
            <button
              onClick={() => router.back()}
              className="w-full mt-4 text-gray-600 py-3 font-medium hover:text-gray-900 transition-colors"
            >
              돌아가기
            </button>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
