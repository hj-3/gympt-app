'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { confirmSignUp } from 'aws-amplify/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import toast from 'react-hot-toast';

export default function SignupPage() {
  const router = useRouter();
  const { signup, login } = useAuthStore();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState('');
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
      toast.success('인증 코드가 이메일로 전송되었습니다!');
      setNeedsConfirmation(true);
    } catch (error: any) {
      let errorMessage = '회원가입에 실패했습니다';

      if (error.message?.includes('UsernameExistsException') || error.message?.includes('already exists')) {
        errorMessage = '이미 가입된 이메일입니다. 로그인해주세요.';
      } else if (error.message?.includes('InvalidPasswordException')) {
        errorMessage = '비밀번호는 대문자, 소문자, 숫자, 특수문자를 각각 포함해야 합니다';
      } else {
        errorMessage = error.message || errorMessage;
      }

      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmation = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!confirmationCode || confirmationCode.length !== 6) {
      toast.error('6자리 인증 코드를 입력해주세요');
      return;
    }

    setLoading(true);

    try {
      await confirmSignUp({
        username: email,
        confirmationCode,
      });

      toast.success('이메일 인증 완료! 로그인 중...');

      // Auto login after confirmation
      await login(email, password);
      router.push('/dashboard');
    } catch (error: any) {
      let errorMessage = '인증에 실패했습니다';

      if (error.message?.includes('CodeMismatchException')) {
        errorMessage = '인증 코드가 일치하지 않습니다';
      } else if (error.message?.includes('ExpiredCodeException')) {
        errorMessage = '인증 코드가 만료되었습니다. 다시 회원가입해주세요.';
      } else {
        errorMessage = error.message || errorMessage;
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
            {needsConfirmation ? '이메일 인증' : '회원가입'}
          </h2>
          <p className="mt-2 text-gray-600">
            {needsConfirmation
              ? '이메일로 전송된 6자리 인증 코드를 입력하세요'
              : 'GYMPT와 함께 건강한 습관을 시작하세요'}
          </p>
        </div>

        {needsConfirmation ? (
          <form onSubmit={handleConfirmation} className="space-y-6">
            <Input
              label="인증 코드"
              type="text"
              value={confirmationCode}
              onChange={(e) => setConfirmationCode(e.target.value)}
              placeholder="123456"
              maxLength={6}
              required
            />

            <Button type="submit" fullWidth disabled={loading}>
              {loading ? '인증 중...' : '인증 완료'}
            </Button>

            <div className="text-center text-sm">
              <button
                type="button"
                onClick={() => setNeedsConfirmation(false)}
                className="text-blue-600 hover:underline"
              >
                다시 회원가입하기
              </button>
            </div>
          </form>
        ) : (
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
        )}

        {!needsConfirmation && (
          <div className="text-center text-sm">
            <span className="text-gray-600">이미 계정이 있으신가요? </span>
            <Link href="/login" className="text-blue-600 hover:underline font-semibold">
              로그인
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
