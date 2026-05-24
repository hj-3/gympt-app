'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/lib/store';
import { configureAmplify } from '@/lib/amplify-config';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const loadUser = useAuthStore((state) => state.loadUser);

  useEffect(() => {
    // Configure Amplify on client side
    configureAmplify();

    // Load user from Cognito
    loadUser();
  }, [loadUser]);

  return <>{children}</>;
}
