'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';


          {/* Weekly Goal */}
          <div className="bg-white rounded-3xl p-6 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              주간 목표
            </h3>
            <div className="mb-3">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">이번 주 운동</span>
                <span className="font-semibold text-gray-900">
                  {stats.totalWorkouts % 7} / 4회
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all"
                  style={{ width: `${Math.min((stats.totalWorkouts % 7) / 4 * 100, 100)}%` }}
                />
              </div>
            </div>
            <p className="text-sm text-gray-500">
              목표 달성까지 {Math.max(4 - (stats.totalWorkouts % 7), 0)}회 남았어요!
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

function SessionCard({ session }: { session: any }) {
  return (
    <Link href={`/report/detail?sessionId=${session.sessionId || session.reportId}`}>
      <div className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-xl transition-colors cursor-pointer">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">
            {session.summary?.exercisesCompleted || 0}개 운동 완료
          </p>
          <p className="text-xs text-gray-500">
            {new Date(session.completedAt).toLocaleDateString('ko-KR')}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold text-blue-600">
            {session.summary?.averagePostureScore?.toFixed(1) || 0}점
          </p>
          <p className="text-xs text-gray-500">
            {session.summary?.totalDuration || 0}분
          </p>
        </div>
      </div>
    </Link>
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
