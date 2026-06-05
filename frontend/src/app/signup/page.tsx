'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/lib/store';
import { confirmSignUp } from 'aws-amplify/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { apiClient } from '@/lib/api-client';
import toast from 'react-hot-toast';

export default function SignupPage() {
  const router = useRouter();
  const { signup, login } = useAuthStore();
  const [username, setUsername] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState<'MALE' | 'FEMALE' | 'OTHER' | ''>('');
  const [loading, setLoading] = useState(false);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState('');
  const [errors, setErrors] = useState({
    username: '',
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    phoneNumber: '',
    age: '',
    gender: '',
  });

  const validateForm = () => {
    const newErrors = {
      username: '',
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      phoneNumber: '',
      age: '',
      gender: '',
    };

    if (!/^[a-z0-9_]+$/.test(username) || username.length < 3) {
      newErrors.username = '사용자명은 영문 소문자, 숫자, 언더스코어만 사용 가능하며 3자 이상이어야 합니다';
    }

    if (name.length < 2) {
      newErrors.name = '이름은 2자 이상이어야 합니다';
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = '유효한 이메일 주소를 입력해주세요';
    }

    if (password.length < 8) {
      newErrors.password = '비밀번호는 8자 이상이어야 합니다';
    } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).*$/.test(password)) {
      newErrors.password = '비밀번호는 대문자, 소문자, 숫자, 특수문자를 각각 최소 1개 포함해야 합니다';
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = '비밀번호가 일치하지 않습니다';
    }

    // Phone number validation (E.164 format: +821012345678)
    if (phoneNumber && !/^\+[1-9]\d{1,14}$/.test(phoneNumber)) {
      newErrors.phoneNumber = '전화번호는 +821012345678 형식으로 입력해주세요';
    }

    if (!phoneNumber) {
      newErrors.phoneNumber = '전화번호는 필수입니다';
    }

    const ageNum = Number(age);
    if (!age || !Number.isInteger(ageNum) || ageNum < 13 || ageNum > 120) {
      newErrors.age = '나이는 13세 이상 120세 이하로 입력해주세요';
    }

    if (!gender) {
      newErrors.gender = '성별을 선택해주세요';
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
      await signup(username, email, password, name, phoneNumber);
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
        username,
        confirmationCode,
      });

      toast.success('이메일 인증 완료! 로그인 중...');

      // Auto login after confirmation
      await login(username, password);

      // Save one-time profile info (age/gender) to DB.
      // The DB user row is created on first authenticated request, so this runs after login.
      try {
        await apiClient.updateCurrentUserProfile({
          age: Number(age),
          gender,
        });
      } catch (profileError) {
        console.error('Failed to save age/gender to profile:', profileError);
        // Non-blocking: 프로필 저장 실패해도 가입 흐름은 계속 진행
      }

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
            label="사용자명 (로그인 ID)"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value.toLowerCase())}
            placeholder="예: gympt_user123"
            error={errors.username}
            helperText="영문 소문자, 숫자, 언더스코어만 사용 (3자 이상)"
            required
          />

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
            label="나이"
            type="number"
            min={13}
            max={120}
            value={age}
            onChange={(e) => setAge(e.target.value)}
            placeholder="예: 28"
            error={errors.age}
            helperText="가입 시 1회만 입력합니다 (운동 추천에 활용)"
            required
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              성별 <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'MALE', label: '남성' },
                { value: 'FEMALE', label: '여성' },
                { value: 'OTHER', label: '기타' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setGender(opt.value as 'MALE' | 'FEMALE' | 'OTHER')}
                  className={`px-4 py-2 rounded-lg border text-sm font-medium transition-colors ${
                    gender === opt.value
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {errors.gender && (
              <p className="mt-1 text-sm text-red-500">{errors.gender}</p>
            )}
          </div>

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
            label="전화번호"
            type="tel"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            placeholder="+821012345678"
            error={errors.phoneNumber}
            helperText="국제 전화번호 형식 (+82로 시작)"
            required
          />

          <Input
            label="비밀번호"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="예: Gympt1234!"
            error={errors.password}
            helperText="대문자, 소문자, 숫자, 특수문자 각 1개 이상, 8자 이상"
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
