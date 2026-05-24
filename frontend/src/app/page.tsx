'use client';

import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import { ArrowRightIcon, VideoCameraIcon, ChartBarIcon, BoltIcon } from '@heroicons/react/24/outline';

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      {/* Hero Section */}
      <div className="max-w-md mx-auto px-4 pt-12 pb-8">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-600 rounded-2xl mb-6">
            <BoltIcon className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            GYMPT
          </h1>
          <p className="text-lg text-gray-600">
            스마트 피트니스 트레이너
          </p>
        </div>

        {/* CTA Button */}
        {user ? (
          <Link href="/session">
            <Button className="w-full h-14 text-lg font-semibold bg-blue-600 hover:bg-blue-700 rounded-2xl shadow-lg">
              운동 시작하기
              <ArrowRightIcon className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        ) : (
          <Link href="/login">
            <Button className="w-full h-14 text-lg font-semibold bg-blue-600 hover:bg-blue-700 rounded-2xl shadow-lg">
              시작하기
              <ArrowRightIcon className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        )}

        {/* Features */}
        <div className="mt-12 space-y-4">
          <FeatureItem
            icon={<VideoCameraIcon className="w-6 h-6" />}
            title="실시간 자세 분석"
            description="카메라로 운동 자세를 실시간 체크"
          />
          <FeatureItem
            icon={<ChartBarIcon className="w-6 h-6" />}
            title="맞춤형 운동 추천"
            description="나에게 꼭 맞는 운동 프로그램"
          />
          <FeatureItem
            icon={<BoltIcon className="w-6 h-6" />}
            title="즉각적인 피드백"
            description="운동 중 실시간 음성 가이드"
          />
        </div>

        {/* How it Works */}
        <div className="mt-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            사용 방법
          </h2>
          <div className="space-y-4">
            <StepItem number={1} text="로그인 후 운동 시작 버튼 클릭" />
            <StepItem number={2} text="카메라 권한 허용" />
            <StepItem number={3} text="운동하면서 실시간 피드백 받기" />
          </div>
        </div>

        {!user && (
          <div className="mt-12 text-center">
            <p className="text-sm text-gray-500 mb-4">
              아직 계정이 없으신가요?
            </p>
            <Link href="/signup">
              <Button variant="outline" className="w-full rounded-2xl">
                회원가입
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

function FeatureItem({ icon, title, description }: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start space-x-4 p-4 bg-white rounded-2xl shadow-sm">
      <div className="flex-shrink-0 w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <h3 className="text-base font-semibold text-gray-900 mb-1">
          {title}
        </h3>
        <p className="text-sm text-gray-600">
          {description}
        </p>
      </div>
    </div>
  );
}

function StepItem({ number, text }: { number: number; text: string }) {
  return (
    <div className="flex items-center space-x-4 p-4 bg-white rounded-2xl shadow-sm">
      <div className="flex-shrink-0 w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
        {number}
      </div>
      <p className="text-base text-gray-900">{text}</p>
    </div>
  );
}
