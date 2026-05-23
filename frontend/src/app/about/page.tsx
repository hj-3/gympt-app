import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20">
        <div className="container mx-auto px-4">
          <h1 className="text-5xl font-bold mb-6">About GYMPT</h1>
          <p className="text-xl max-w-2xl">
            AI와 컴퓨터 비전 기술을 활용하여 개인화된 피트니스 경험을 제공합니다
          </p>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-4xl font-bold text-center mb-12">Our Mission</h2>
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h3 className="text-2xl font-semibold mb-4">모두를 위한 스마트 피트니스</h3>
              <p className="text-gray-700 leading-relaxed mb-4">
                GYMPT는 최첨단 AI 기술과 컴퓨터 비전을 활용하여 누구나 전문가 수준의
                운동 지도를 받을 수 있도록 합니다. 실시간 자세 분석을 통해 부상을
                예방하고 운동 효과를 극대화합니다.
              </p>
              <p className="text-gray-700 leading-relaxed">
                우리의 목표는 개인의 신체 특성과 운동 목표에 맞춘 완전히 맞춤화된
                피트니스 경험을 제공하는 것입니다.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section className="py-16 bg-gray-100">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-12">Core Technology</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="text-4xl mb-4">🤖</div>
              <h3 className="text-xl font-semibold mb-3">AI 운동 코치</h3>
              <p className="text-gray-600">
                Claude 기반 대화형 AI가 실시간으로 운동을 지도하고
                동기부여를 제공합니다
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="text-4xl mb-4">👁️</div>
              <h3 className="text-xl font-semibold mb-3">실시간 자세 분석</h3>
              <p className="text-gray-600">
                컴퓨터 비전으로 운동 자세를 정밀 분석하고
                즉각적인 피드백을 제공합니다
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-xl font-semibold mb-3">개인화 추천</h3>
              <p className="text-gray-600">
                운동 기록과 신체 데이터를 분석하여
                최적의 운동 계획을 추천합니다
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Team Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-12">Our Values</h2>
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-3">🎯 정확성</h3>
              <p className="text-gray-600">
                정밀한 자세 분석과 데이터 기반 피드백으로
                정확한 운동 효과를 제공합니다
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-3">🔒 안전</h3>
              <p className="text-gray-600">
                실시간 모니터링으로 부상 위험을 사전에 감지하고
                안전한 운동 환경을 보장합니다
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-3">💡 혁신</h3>
              <p className="text-gray-600">
                최신 AI 기술을 활용하여 계속해서
                더 나은 피트니스 경험을 만들어갑니다
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-3">🤝 접근성</h3>
              <p className="text-gray-600">
                언제 어디서나 전문가 수준의 운동 지도를
                받을 수 있도록 합니다
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-blue-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-6">지금 시작하세요</h2>
          <p className="text-xl mb-8">AI 기반 스마트 피트니스의 새로운 경험</p>
          <div className="flex gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100">
                무료로 시작하기
              </Button>
            </Link>
            <Link href="/features">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-blue-700">
                기능 살펴보기
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
