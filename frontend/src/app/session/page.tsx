'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// /session 페이지는 /workout 으로 통합되었습니다.
// 기존 북마크/외부 링크 호환을 위해 리다이렉트만 수행합니다.
export default function SessionRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/workout');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
    </div>
  );
}
