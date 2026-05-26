'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  HomeIcon,
  PlayIcon,
  ChartBarIcon,
  UserCircleIcon
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  PlayIcon as PlayIconSolid,
  ChartBarIcon as ChartBarIconSolid,
  UserCircleIcon as UserCircleIconSolid
} from '@heroicons/react/24/solid';

const navItems = [
  { href: '/', label: '홈', icon: HomeIcon, activeIcon: HomeIconSolid },
  { href: '/session', label: '운동 시작', icon: PlayIcon, activeIcon: PlayIconSolid },
  { href: '/dashboard', label: '대시보드', icon: ChartBarIcon, activeIcon: ChartBarIconSolid },
  { href: '/profile', label: '내 정보', icon: UserCircleIcon, activeIcon: UserCircleIconSolid },
];

export function BottomNav() {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Prevent hydration mismatch by not rendering active state until mounted
  if (!mounted) {
    return (
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-area-inset-bottom z-50">
        <div className="max-w-md mx-auto">
          <div className="flex justify-around items-center h-16">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="flex flex-col items-center justify-center flex-1 h-full transition-colors text-gray-500"
              >
                <item.icon className="w-6 h-6 mb-1" />
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            ))}
          </div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-area-inset-bottom z-50">
      <div className="max-w-md mx-auto">
        <div className="flex justify-around items-center h-16">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = isActive ? item.activeIcon : item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                  isActive
                    ? 'text-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Icon className="w-6 h-6 mb-1" />
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
