'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api-client';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { RecentSessions } from '@/components/dashboard/RecentSessions';
import { WeeklyChart } from '@/components/dashboard/WeeklyChart';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import toast from 'react-hot-toast';

interface DashboardStats {
  totalMinutes?: number;
  completedSessions?: number;
  avgPostureScore?: number;
  weeklyWorkouts?: number;
  recentSessions?: any[];
  weeklyData?: any[];
  todayRoutine?: any;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    const loadData = async () => {
      if (!user) return;

      try {
        const statsRes = await apiClient.getStats(user.userId);
        setStats(statsRes.data);
      } catch (error: any) {
        console.error('Failed to load dashboard data:', error);
        // Set empty stats instead of showing error
        setStats({
          totalMinutes: 0,
          completedSessions: 0,
          avgPostureScore: 0,
          weeklyWorkouts: 0,
          recentSessions: [],
          weeklyData: [],
        });
        // toast.error('데이터를 불러오는데 실패했습니다');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user, isAuthenticated, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">
            안녕하세요, {user.name}님!
          </h1>
          <p className="text-gray-600">오늘도 건강한 하루 되세요</p>
        </div>
        <div className="flex gap-2">
          <Link href="/profile">
            <Button variant="secondary">신체 정보</Button>
          </Link>
          <Link href="/workout">
            <Button>운동 시작</Button>
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid md:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="총 운동 시간"
          value={stats?.totalMinutes || 0}
          unit="분"
          icon="⏱️"
        />
        <StatsCard
          title="완료한 세션"
          value={stats?.completedSessions || 0}
          unit="회"
          icon="✅"
        />
        <StatsCard
          title="평균 자세 점수"
          value={stats?.avgPostureScore ? stats.avgPostureScore.toFixed(1) : '0.0'}
          unit="/10"
          icon="🎯"
        />
        <StatsCard
          title="이번 주 운동"
          value={stats?.weeklyWorkouts || 0}
          unit="회"
          icon="📅"
        />
      </div>

      {/* Today's Routine */}
      {stats?.todayRoutine && (
        <Card className="mb-8">
          <h2 className="text-xl font-bold mb-4">오늘의 추천 운동</h2>
          <div>
            <h3 className="text-lg font-semibold mb-2">{stats.todayRoutine.name}</h3>
            <p className="text-gray-600 mb-4">{stats.todayRoutine.description}</p>
            <div className="flex items-center gap-4 mb-4">
              <span className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full">
                {stats.todayRoutine.difficulty}
              </span>
              <span className="text-sm text-gray-600">
                {stats.todayRoutine.duration}분
              </span>
            </div>
            <Link href="/session">
              <Button>운동 시작하기</Button>
            </Link>
          </div>
        </Card>
      )}

      {/* Charts and Recent Sessions */}
      <div className="grid md:grid-cols-2 gap-8">
        <WeeklyChart data={stats?.weeklyData || []} />
        <RecentSessions sessions={stats?.recentSessions || []} />
      </div>
    </div>
  );
}
