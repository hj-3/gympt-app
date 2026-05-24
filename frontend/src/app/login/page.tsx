'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(username, password);
      toast.success('로그인에 성공했습니다!');
      router.push('/dashboard');
    } catch (err: any) {
      let errorMessage = '로그인에 실패했습니다';

      if (err.message?.includes('UserNotFoundException') || err.message?.includes('NotAuthorizedException')) {
        errorMessage = '사용자명 또는 비밀번호가 올바르지 않습니다';
      } else if (err.message?.includes('UserNotConfirmedException')) {
        errorMessage = '이메일 인증이 완료되지 않았습니다. 이메일을 확인해주세요';
      } else {
        errorMessage = err.message || errorMessage;
      }

      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-blue-600 mb-2">GYMPT</h1>
          <h2 className="text-2xl font-semibold text-gray-700">
            로그인
          </h2>
          <p className="mt-2 text-gray-600">
            GYMPT 계정으로 로그인하세요
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            label="사용자명"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="회원가입 시 입력한 사용자명"
            required
          />

          <Input
            label="비밀번호"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="비밀번호를 입력하세요"
            required
            error={error}
          />

          <Button
            type="submit"
            fullWidth
            disabled={loading}
          >
            {loading ? '로그인 중...' : '로그인'}
          </Button>
        </form>

        <div className="text-center text-sm">
          <span className="text-gray-600">계정이 없으신가요? </span>
          <Link href="/signup" className="text-blue-600 hover:underline font-semibold">
            회원가입
          </Link>
        </div>
      </div>
    </div>
  );
}
