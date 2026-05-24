'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { ChevronLeftIcon } from '@heroicons/react/24/outline';

export default function ProfileInfoPage() {
  const router = useRouter();
  const { user } = useAuth();

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
              내 정보
            </h1>
          </div>

          {/* Content */}
          <div className="px-4 py-6 space-y-4">
            {/* Basic Info */}
            <div className="bg-white rounded-3xl p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                기본 정보
              </h2>
              <div className="space-y-3">
                <InfoRow label="이름" value={user?.attributes?.name || '정보 없음'} />
                <InfoRow label="이메일" value={user?.attributes?.email || '정보 없음'} />
                <InfoRow label="전화번호" value={user?.attributes?.phone_number || '정보 없음'} />
              </div>
            </div>

            {/* Body Info */}
            <div className="bg-white rounded-3xl p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                신체 정보
              </h2>
              <div className="space-y-3">
                <InfoRow label="키" value="175 cm" editable />
                <InfoRow label="체중" value="70 kg" editable />
                <InfoRow label="나이" value="28세" editable />
                <InfoRow label="성별" value="남성" editable />
              </div>
            </div>

            {/* Account Actions */}
            <div className="space-y-3 pt-4">
              <button
                onClick={() => router.push('/profile/change-password')}
                className="w-full bg-white rounded-2xl p-4 shadow-sm text-left hover:bg-gray-50 transition-colors"
              >
                <span className="text-base font-medium text-gray-900">
                  비밀번호 변경
                </span>
              </button>
              <button
                onClick={() => {
                  if (confirm('정말로 회원 탈퇴하시겠습니까?')) {
                    // TODO: Implement account deletion
                    alert('회원 탈퇴 기능은 준비 중입니다.');
                  }
                }}
                className="w-full bg-white rounded-2xl p-4 shadow-sm text-left hover:bg-red-50 transition-colors"
              >
                <span className="text-base font-medium text-red-600">
                  회원 탈퇴
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function InfoRow({ label, value, editable = false }: { label: string; value: string; editable?: boolean }) {
  return (
    <div className="flex justify-between items-center py-2">
      <span className="text-sm text-gray-600">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-900">{value}</span>
        {editable && (
          <button className="text-xs text-blue-600 hover:text-blue-700">
            수정
          </button>
        )}
      </div>
    </div>
  );
}
