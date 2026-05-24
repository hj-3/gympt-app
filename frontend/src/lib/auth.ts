import { signIn, signUp, signOut, getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';

export interface CognitoUser {
  userId: string;
  email: string;
  name: string;
  emailVerified: boolean;
}

export async function loginWithCognito(username: string, password: string): Promise<CognitoUser> {
  const { isSignedIn } = await signIn({
    username,
    password,
  });

  if (!isSignedIn) {
    throw new Error('Sign in failed');
  }

  return await getCurrentCognitoUser();
}

export async function signupWithCognito(
  username: string,
  email: string,
  password: string,
  name: string,
  phoneNumber?: string
): Promise<{ userId: string; email: string }> {
  const userAttributes: any = {
    email,
    name,
  };

  // Add phone_number if provided
  if (phoneNumber) {
    userAttributes.phone_number = phoneNumber;
  }

  const { userId, isSignUpComplete } = await signUp({
    username,
    password,
    options: {
      userAttributes,
    },
  });

  return { userId: userId || '', email };
}

export async function logoutFromCognito(): Promise<void> {
  await signOut();
}

export async function getCurrentCognitoUser(): Promise<CognitoUser> {
  const user = await getCurrentUser();
  const { tokens } = await fetchAuthSession();

  const idToken = tokens?.idToken;
  const payload = idToken?.payload;

  return {
    userId: user.userId,
    email: (payload?.email as string) || '',
    name: (payload?.name as string) || user.username,
    emailVerified: (payload?.email_verified as boolean) || false,
  };
}

export async function getAuthToken(): Promise<string | undefined> {
  try {
    const { tokens } = await fetchAuthSession();
    return tokens?.idToken?.toString();
  } catch {
    return undefined;
  }
}

export async function isAuthenticated(): Promise<boolean> {
  try {
    await getCurrentUser();
    return true;
  } catch {
    return false;
  }
}
