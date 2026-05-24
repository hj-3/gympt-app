import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Toaster } from 'react-hot-toast';
import { BottomNav } from '@/components/layout/BottomNav';
import { AuthProvider } from '@/components/providers/AuthProvider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'GYMPT - 스마트 피트니스 트레이너',
  description: '실시간 AI 자세 분석으로 더 안전하고 효과적인 운동',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <AuthProvider>
          <div className="flex flex-col min-h-screen bg-gray-50">
            <main className="flex-1 pb-20">{children}</main>
            <BottomNav />
          </div>
          <Toaster position="top-center" />
        </AuthProvider>
      </body>
    </html>
  );
}
