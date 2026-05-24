import { signIn, signUp, signOut, getCurrentUser, fetchAuthSession } from 'aws-amplify/auth';

export interface CognitoUser {
  userId: string;
  email: string;
  name: string;
  emailVerified: boolean;
}

export async function loginWithCognito(email: string, password: string): Promise<CognitoUser> {
  // Try login with email first, fallback to username
  try {
    const { isSignedIn } = await signIn({
      username: email,
      password,
    });

    if (!isSignedIn) {
      throw new Error('Sign in failed');
    }

    return await getCurrentCognitoUser();
  } catch (error: any) {
    // If email login fails, try with username format
    if (error.message?.includes('UserNotFoundException')) {
      const username = email.split('@')[0].toLowerCase();
      const { isSignedIn } = await signIn({
        username,
        password,
      });

      if (!isSignedIn) {
        throw new Error('Sign in failed');
      }

      return await getCurrentCognitoUser();
    }
    throw error;
  }
}

export async function signupWithCognito(
  email: string,
  password: string,
  name: string
): Promise<{ userId: string; email: string }> {
  // Generate username from email (without @ and domain)
  const username = email.split('@')[0].toLowerCase();

  const { userId, isSignUpComplete } = await signUp({
    username,
    password,
    options: {
      userAttributes: {
        email,
        name,
      },
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
