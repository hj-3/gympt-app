'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import toast from 'react-hot-toast';

export default function SignupPage() {
  const router = useRouter();
  const { signup } = useAuthStore();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const validateForm = () => {
    const newErrors = {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
    };

    if (name.length < 2) {
      newErrors.name = '이름은 2자 이상이어야 합니다';
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = '유효한 이메일 주소를 입력해주세요';
    }

    if (password.length < 8) {
      newErrors.password = '비밀번호는 8자 이상이어야 합니다';
    } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).*$/.test(password)) {
      newErrors.password = '비밀번호는 대문자, 소문자, 숫자를 각각 최소 1개 포함해야 합니다';
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = '비밀번호가 일치하지 않습니다';
    }

    setErrors(newErrors);
    return !Object.values(newErrors).some((error) => error !== '');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      await signup(email, password, name);
      toast.success('계정이 생성되었습니다!');
      router.push('/dashboard');
    } catch (error: any) {
      let errorMessage = '회원가입에 실패했습니다';

      if (error.response?.status === 400) {
        const message = error.response?.data?.error?.message || error.response?.data?.message;
        if (message?.includes('already exists') || message?.includes('이미 존재')) {
          errorMessage = '이미 가입된 이메일입니다. 로그인해주세요.';
        } else if (message?.includes('Password')) {
          errorMessage = '비밀번호는 대문자, 소문자, 숫자를 각각 포함해야 합니다';
        } else {
          errorMessage = message || errorMessage;
        }
      }

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
            회원가입
          </h2>
          <p className="mt-2 text-gray-600">
            GYMPT와 함께 건강한 습관을 시작하세요
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            label="이름"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="홍길동"
            error={errors.name}
            required
          />

          <Input
            label="이메일"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
            error={errors.email}
            required
          />

          <Input
            label="비밀번호"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="예: Gympt1234"
            error={errors.password}
            helperText="대문자, 소문자, 숫자 각 1개 이상, 8자 이상"
            required
          />

          <Input
            label="비밀번호 확인"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="비밀번호를 다시 입력하세요"
            error={errors.confirmPassword}
            required
          />

          <Button
            type="submit"
            fullWidth
            disabled={loading}
          >
            {loading ? '계정 생성 중...' : '회원가입'}
          </Button>
        </form>

        <div className="text-center text-sm">
          <span className="text-gray-600">이미 계정이 있으신가요? </span>
          <Link href="/login" className="text-blue-600 hover:underline font-semibold">
            로그인
          </Link>
        </div>
      </div>
    </div>
  );
}
