'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import {
  UserCircleIcon,
  UserIcon,
  ChartBarIcon,
  BellIcon,
  QuestionMarkCircleIcon,
  DocumentTextIcon,
  ArrowRightOnRectangleIcon,
  ChevronRightIcon,
  SparklesIcon,
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
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-1">
              내 정보
            </h1>
            <p className="text-sm text-gray-600">
              계정 및 설정 관리
            </p>
          </div>

          {/* User Card */}
          <button
            onClick={() => router.push('/profile/info')}
            className="w-full bg-white rounded-3xl p-6 mb-6 shadow-sm hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                <UserCircleIcon className="w-10 h-10 text-blue-600" />
              </div>
              <div className="flex-1 min-w-0 text-left">
                <h2 className="text-lg font-semibold text-gray-900 truncate">
                  {user?.attributes?.name || user?.username || '사용자'}
                </h2>
                <p className="text-sm text-gray-500">
                  {user?.attributes?.email || 'GYMPT 회원'}
                </p>
              </div>
              <ChevronRightIcon className="w-5 h-5 text-gray-400" />
            </div>
          </button>

          {/* Menu Items */}
          <div className="bg-white rounded-3xl shadow-sm overflow-hidden mb-6">
            <MenuItem
              icon={UserIcon}
              label="내 정보"
              onClick={() => router.push('/profile/info')}
            />
            <MenuItem
              icon={ChartBarIcon}
              label="인바디 정보"
              onClick={() => router.push('/profile/body')}
            />
            <MenuItem
              icon={SparklesIcon}
              label="AI 코치 추천"
              onClick={() => router.push('/profile/ai-coach')}
            />
            <MenuItem
              icon={BellIcon}
              label="알림 설정"
              onClick={() => toast('준비 중입니다')}
            />
            <MenuItem
              icon={QuestionMarkCircleIcon}
              label="고객센터"
              onClick={() => toast('준비 중입니다')}
            />
            <MenuItem
              icon={DocumentTextIcon}
              label="이용약관"
              onClick={() => router.push('/terms')}
              showDivider={false}
            />
          </div>

          {/* Sign Out Button */}
          <button
            onClick={handleSignOut}
            className="w-full bg-white rounded-3xl p-5 shadow-sm flex items-center justify-center space-x-3 text-red-600 font-medium hover:bg-red-50 transition-colors"
          >
            <ArrowRightOnRectangleIcon className="w-6 h-6" />
            <span>로그아웃</span>
          </button>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-gray-500">
            <p>GYMPT v0.2.0</p>
            <p className="mt-1">© 2026 GYMPT. All rights reserved.</p>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function MenuItem({
  icon: Icon,
  label,
  onClick,
  showDivider = true,
}: {
  icon: any;
  label: string;
  onClick?: () => void;
  showDivider?: boolean;
}) {
  return (
    <>
      <button
        onClick={onClick}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center space-x-3">
          <Icon className="w-6 h-6 text-gray-600" />
          <span className="text-base text-gray-900">{label}</span>
        </div>
        <ChevronRightIcon className="w-5 h-5 text-gray-400" />
      </button>
      {showDivider && <div className="border-t border-gray-100 mx-6" />}
    </>
  );
}
