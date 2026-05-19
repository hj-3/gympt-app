import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-16">
      <section className="text-center mb-16">
        <h1 className="text-5xl font-bold mb-4 text-gray-900">
          AI 기반 개인화 피트니스
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          실시간 자세 분석으로 안전하고 효과적인 운동을
        </p>
        <div className="flex gap-4 justify-center">
          <Link href="/login">
            <Button size="lg">시작하기</Button>
          </Link>
          <Link href="/about">
            <Button variant="outline" size="lg">더 알아보기</Button>
          </Link>
        </div>
      </section>

      <section className="grid md:grid-cols-3 gap-8 mb-16">
        <FeatureCard
          icon="🤖"
          title="AI 추천"
          description="AWS Bedrock 기반 맞춤형 운동 계획"
        />
        <FeatureCard
          icon="📹"
          title="실시간 분석"
          description="MediaPipe로 정확한 자세 교정"
        />
        <FeatureCard
          icon="📊"
          title="진척도 추적"
          description="데이터 기반 성과 분석"
        />
      </section>

      <section className="bg-blue-50 rounded-2xl p-8 md:p-12">
        <h2 className="text-3xl font-bold text-center mb-8">주요 기능</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="flex items-start space-x-4">
            <div className="text-2xl">✓</div>
            <div>
              <h3 className="font-semibold mb-1">실시간 자세 분석</h3>
              <p className="text-gray-600">MediaPipe를 활용한 정확한 신체 랜드마크 추적</p>
            </div>
          </div>
          <div className="flex items-start space-x-4">
            <div className="text-2xl">✓</div>
            <div>
              <h3 className="font-semibold mb-1">AI 개인화 추천</h3>
              <p className="text-gray-600">Claude 3를 통한 맞춤형 운동 프로그램</p>
            </div>
          </div>
          <div className="flex items-start space-x-4">
            <div className="text-2xl">✓</div>
            <div>
              <h3 className="font-semibold mb-1">진행도 대시보드</h3>
              <p className="text-gray-600">운동 기록과 성과를 한눈에 확인</p>
            </div>
          </div>
          <div className="flex items-start space-x-4">
            <div className="text-2xl">✓</div>
            <div>
              <h3 className="font-semibold mb-1">안전한 클라우드 저장</h3>
              <p className="text-gray-600">AWS 기반 보안 인프라</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, description }: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <div className="text-center">
        <div className="text-5xl mb-4">{icon}</div>
        <h3 className="text-xl font-semibold mb-2">{title}</h3>
        <p className="text-gray-600">{description}</p>
      </div>
    </Card>
  );
}
