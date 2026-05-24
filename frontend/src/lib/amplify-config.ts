import { Amplify } from 'aws-amplify';

const amplifyConfig = {
  Auth: {
    Cognito: {
      userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || '',
      userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || '',
      region: process.env.NEXT_PUBLIC_AWS_REGION || 'ap-northeast-2',
      loginWith: {
        email: true,
      },
    },
  },
};

export function configureAmplify() {
  Amplify.configure(amplifyConfig, { ssr: true });
}

export default amplifyConfig;
