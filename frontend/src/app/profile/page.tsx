'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import {
  UserCircleIcon,
  BellIcon,
  ShieldCheckIcon,
  QuestionMarkCircleIcon,
  ArrowRightOnRectangleIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import toast from 'react-hot-toast';

export default function ProfilePage() {
  const router = useRouter();
  const { user, signOut } = useAuth();

  const handleSignOut = async () => {
    try {
      await signOut();
      toast.success('로그아웃되었습니다');
      router.push('/');
    } catch (error) {
      toast.error('로그아웃에 실패했습니다');
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto px-4 py-6">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-1">
              내 정보
            </h1>
            <p className="text-sm text-gray-600">
              계정 및 설정 관리
            </p>
          </div>

          <div className="bg-white rounded-3xl p-6 mb-6 shadow-sm">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                <UserCircleIcon className="w-10 h-10 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0">
                <h2 className="text-lg font-semibold text-gray-900 truncate">
                  {user?.email || '사용자'}
                </h2>
                <p className="text-sm text-gray-500">
                  GYMPT 회원
                </p>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-400" />
            </div>
          </div>

          <button
            onClick={handleSignOut}
            className="w-full bg-white rounded-3xl p-5 shadow-sm flex items-center justify-center space-x-3 text-red-600 font-medium hover:bg-red-50 transition-colors"
          >
            <ArrowRightOnRectangleIcon className="w-6 h-6" />
            <span>로그아웃</span>
          </button>

          <div className="mt-8 text-center text-sm text-gray-500">
            <p>GYMPT v1.0.0</p>
            <p className="mt-1">© 2026 GYMPT. All rights reserved.</p>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
