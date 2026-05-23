import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20">
        <div className="container mx-auto px-4">
          <h1 className="text-5xl font-bold mb-6">Features</h1>
          <p className="text-xl max-w-2xl">
            GYMPT의 강력한 기능으로 당신의 피트니스 목표를 달성하세요
          </p>
        </div>
      </section>

      {/* Main Features */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-12">핵심 기능</h2>

          {/* Feature 1 */}
          <div className="max-w-6xl mx-auto mb-16">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="text-6xl mb-6">🤖</div>
                <h3 className="text-3xl font-bold mb-4">AI 운동 코치</h3>
                <p className="text-gray-700 text-lg leading-relaxed mb-4">
                  Claude AI 기반 대화형 코치가 실시간으로 운동을 지도합니다.
                  운동 중 질문하고 즉각적인 피드백을 받으세요.
                </p>
                <ul className="space-y-2 text-gray-700">
                  <li>✓ 자연어 대화로 운동 지도</li>
                  <li>✓ 개인 맞춤형 동기부여</li>
                  <li>✓ 실시간 운동 조언</li>
                  <li>✓ 운동 기록 자동 분석</li>
                </ul>
              </div>
              <div className="bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg p-8 h-64 flex items-center justify-center">
                <p className="text-2xl font-semibold text-blue-800">AI Coach Demo</p>
              </div>
            </div>
          </div>

          {/* Feature 2 */}
          <div className="max-w-6xl mx-auto mb-16 bg-gray-100 rounded-lg p-8">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div className="order-2 md:order-1 bg-gradient-to-br from-green-100 to-green-200 rounded-lg p-8 h-64 flex items-center justify-center">
                <p className="text-2xl font-semibold text-green-800">Posture Analysis Demo</p>
              </div>
              <div className="order-1 md:order-2">
                <div className="text-6xl mb-6">👁️</div>
                <h3 className="text-3xl font-bold mb-4">실시간 자세 분석</h3>
                <p className="text-gray-700 text-lg leading-relaxed mb-4">
                  컴퓨터 비전 기술로 운동 자세를 정밀하게 분석하고
                  부상을 예방합니다.
                </p>
                <ul className="space-y-2 text-gray-700">
                  <li>✓ 25개 관절 포인트 실시간 추적</li>
                  <li>✓ 자세 정확도 점수 제공</li>
                  <li>✓ 잘못된 자세 즉시 교정</li>
                  <li>✓ 부상 위험 사전 감지</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Feature 3 */}
          <div className="max-w-6xl mx-auto mb-16">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <div className="text-6xl mb-6">📊</div>
                <h3 className="text-3xl font-bold mb-4">개인화 운동 계획</h3>
                <p className="text-gray-700 text-lg leading-relaxed mb-4">
                  신체 데이터와 운동 목표를 기반으로 최적의 운동 루틴을
                  자동으로 생성합니다.
                </p>
                <ul className="space-y-2 text-gray-700">
                  <li>✓ 체형 분석 기반 맞춤 운동</li>
                  <li>✓ 목표 달성을 위한 단계별 계획</li>
                  <li>✓ 진행 상황 자동 추적</li>
                  <li>✓ 주간/월간 성과 리포트</li>
                </ul>
              </div>
              <div className="bg-gradient-to-br from-purple-100 to-purple-200 rounded-lg p-8 h-64 flex items-center justify-center">
                <p className="text-2xl font-semibold text-purple-800">Workout Plan Demo</p>
              </div>
            </div>
          </div>

          {/* Feature 4 */}
          <div className="max-w-6xl mx-auto mb-16 bg-gray-100 rounded-lg p-8">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div className="order-2 md:order-1 bg-gradient-to-br from-orange-100 to-orange-200 rounded-lg p-8 h-64 flex items-center justify-center">
                <p className="text-2xl font-semibold text-orange-800">Analytics Demo</p>
              </div>
              <div className="order-1 md:order-2">
                <div className="text-6xl mb-6">📈</div>
                <h3 className="text-3xl font-bold mb-4">상세한 분석 리포트</h3>
                <p className="text-gray-700 text-lg leading-relaxed mb-4">
                  운동 데이터를 시각화하고 분석하여 발전 과정을 추적합니다.
                </p>
                <ul className="space-y-2 text-gray-700">
                  <li>✓ 운동별 수행 통계</li>
                  <li>✓ 자세 정확도 추이 분석</li>
                  <li>✓ 칼로리 소모 추정</li>
                  <li>✓ 목표 달성률 시각화</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Additional Features Grid */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold text-center mb-12">추가 기능</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="text-4xl mb-4">⌚</div>
              <h3 className="text-xl font-semibold mb-3">웨어러블 연동</h3>
              <p className="text-gray-600">
                스마트워치와 연동하여 심박수, 활동량 데이터를
                실시간으로 수집합니다
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="text-4xl mb-4">🎥</div>
              <h3 className="text-xl font-semibold mb-3">운동 영상 리플레이</h3>
              <p className="text-gray-600">
                운동 세션을 녹화하고 다시 보며
                자세를 점검할 수 있습니다
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="text-4xl mb-4">🏆</div>
              <h3 className="text-xl font-semibold mb-3">목표 관리</h3>
              <p className="text-gray-600">
                단기/장기 목표를 설정하고
                달성률을 추적합니다
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="text-4xl mb-4">💪</div>
              <h3 className="text-xl font-semibold mb-3">다양한 운동 지원</h3>
              <p className="text-gray-600">
                스쿼트, 푸시업, 플랭크 등
                다양한 운동 종목 지원
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="text-4xl mb-4">🔔</div>
              <h3 className="text-xl font-semibold mb-3">스마트 알림</h3>
              <p className="text-gray-600">
                운동 시간 알림, 목표 달성 축하 등
                맞춤형 알림 제공
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="text-4xl mb-4">📱</div>
              <h3 className="text-xl font-semibold mb-3">크로스 플랫폼</h3>
              <p className="text-gray-600">
                웹, 모바일 어디서나
                동일한 경험 제공
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-6">이 모든 기능을 지금 무료로 체험하세요</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            회원가입 후 바로 AI 코치와 함께 운동을 시작할 수 있습니다
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100">
                무료로 시작하기
              </Button>
            </Link>
            <Link href="/about">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-blue-700">
                더 알아보기
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
