'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import {
  FireIcon,
  CalendarIcon,
  TrophyIcon,
  ChartBarIcon,
  PlayIcon
} from '@heroicons/react/24/outline';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';

interface DashboardStats {
  totalWorkouts: number;
  totalMinutes: number;
  avgScore: number;
  streak: number;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalWorkouts: 0,
    totalMinutes: 0,
    avgScore: 0,
    streak: 0
  });

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-md mx-auto px-4 py-6">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-1">
              대시보드
            </h1>
            <p className="text-sm text-gray-600">
              나의 운동 기록을 확인하세요
            </p>
          </div>

          {/* Quick Action */}
          <Link href="/session">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-3xl p-6 mb-6 shadow-lg">
              <div className="flex items-center justify-between text-white">
                <div>
                  <p className="text-sm font-medium mb-1 opacity-90">지금 바로</p>
                  <h2 className="text-2xl font-bold">운동 시작하기</h2>
                </div>
                <div className="w-14 h-14 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                  <PlayIcon className="w-7 h-7" />
                </div>
              </div>
            </div>
          </Link>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <StatCard
              icon={<FireIcon className="w-6 h-6 text-orange-500" />}
              label="연속 운동"
              value={`${stats.streak}일`}
              bgColor="bg-orange-50"
            />
            <StatCard
              icon={<TrophyIcon className="w-6 h-6 text-yellow-500" />}
              label="총 운동"
              value={`${stats.totalWorkouts}회`}
              bgColor="bg-yellow-50"
            />
            <StatCard
              icon={<CalendarIcon className="w-6 h-6 text-green-500" />}
              label="운동 시간"
              value={`${stats.totalMinutes}분`}
              bgColor="bg-green-50"
            />
            <StatCard
              icon={<ChartBarIcon className="w-6 h-6 text-blue-500" />}
              label="평균 점수"
              value={`${stats.avgScore}점`}
              bgColor="bg-blue-50"
            />
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-3xl p-6 shadow-sm mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                최근 운동
              </h3>
              <Link href="/report">
                <button className="text-sm text-blue-600 font-medium">
                  전체보기
                </button>
              </Link>
            </div>
            <div className="space-y-3">
              <EmptyState message="아직 운동 기록이 없어요" />
            </div>
          </div>

          {/* Weekly Goal */}
          <div className="bg-white rounded-3xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              주간 목표
            </h3>
            <div className="mb-3">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">이번 주 운동</span>
                <span className="font-semibold text-gray-900">0 / 4회</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all"
                  style={{ width: '0%' }}
                />
              </div>
            </div>
            <p className="text-sm text-gray-500">
              목표 달성까지 4회 남았어요!
            </p>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}

function StatCard({ icon, label, value, bgColor }: {
  icon: React.ReactNode;
  label: string;
  value: string;
  bgColor: string;
}) {
  return (
    <div className="bg-white rounded-3xl p-5 shadow-sm">
      <div className={`inline-flex p-2 rounded-xl ${bgColor} mb-3`}>
        {icon}
      </div>
      <p className="text-sm text-gray-600 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-8">
      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
        <ChartBarIcon className="w-8 h-8 text-gray-400" />
      </div>
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  );
}
