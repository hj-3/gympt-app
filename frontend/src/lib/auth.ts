import { signIn, signUp, signOut, getCurrentUser, fetchAuthSession, updatePassword, deleteUser } from 'aws-amplify/auth';

export interface CognitoUser {
  userId: string;
  username?: string;
  email: string;
  name: string;
  emailVerified: boolean;
  attributes?: {
    name?: string;
    email?: string;
    phone_number?: string;
    [key: string]: string | undefined;
  };
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
  // Clear all gympt session data so a re-registering user starts clean
  if (typeof window !== 'undefined') {
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('gympt_')) keysToRemove.push(key);
    }
    keysToRemove.forEach(k => localStorage.removeItem(k));
  }
}

export async function getCurrentCognitoUser(): Promise<CognitoUser> {
  const user = await getCurrentUser();
  const { tokens } = await fetchAuthSession();

  const idToken = tokens?.idToken;
  const payload = idToken?.payload;

  return {
    userId: user.userId,
    username: user.username,
    email: (payload?.email as string) || '',
    name: (payload?.name as string) || user.username,
    emailVerified: (payload?.email_verified as boolean) || false,
    attributes: {
      name: payload?.name as string,
      email: payload?.email as string,
      phone_number: payload?.phone_number as string,
    },
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

export async function deleteCognitoUser(): Promise<void> {
  try {
    await deleteUser();
  } catch (error) {
    console.error('Failed to delete Cognito user:', error);
    throw error;
  }
}

export async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
  await updatePassword({ oldPassword, newPassword });
}
