# GYMPT Frontend

AI 기반 개인화 피트니스 플랫폼 - 실시간 운동 자세 분석

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **State Management:** Zustand
- **Styling:** Tailwind CSS
- **API Client:** Axios
- **Real-time:** WebSocket + AWS Kinesis Video Streams WebRTC
- **Charts:** Recharts

## Features

1. **Authentication**
   - JWT-based auth with access/refresh tokens
   - Auto token refresh on 401
   - Persistent session

2. **Body Profile Management**
   - InBody measurements input
   - BMI calculation
   - Progress tracking

3. **Workout Goals**
   - Goal type selection (muscle gain, weight loss, etc.)
   - Target settings
   - Weekly workout schedule

4. **Today's Routine**
   - AI-generated daily workout plans
   - Exercise details with videos
   - Difficulty-based recommendations

5. **Camera Workout**
   - Real-time video streaming via WebRTC
   - Live posture analysis
   - Instant feedback overlay

6. **Workout Session**
   - Exercise timer
   - Set/rep tracking
   - Real-time posture scoring

7. **Workout Report**
   - Session summary
   - Posture analysis breakdown
   - AI-generated insights

8. **Dashboard**
   - Workout history
   - Progress charts
   - Streak tracking
   - Weekly statistics

## Directory Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── login/             # Login page
│   │   ├── signup/            # Signup page
│   │   ├── dashboard/         # Main dashboard
│   │   ├── profile/           # User profile & body data
│   │   ├── workout/           # Today's workout routine
│   │   ├── session/           # Active workout session
│   │   └── report/            # Workout report
│   ├── components/            # React components
│   │   ├── auth/              # Auth-related components
│   │   ├── workout/           # Workout components
│   │   ├── camera/            # Camera/WebRTC components
│   │   └── dashboard/         # Dashboard components
│   ├── lib/                   # Core libraries
│   │   ├── api-client.ts      # REST API client
│   │   ├── websocket-client.ts # WebSocket client
│   │   ├── kvs-client.ts      # KVS WebRTC client
│   │   └── store.ts           # Zustand stores
│   ├── types/                 # TypeScript types
│   │   └── index.ts           # All type definitions
│   └── hooks/                 # Custom React hooks
├── public/                    # Static files
├── .env.example               # Environment variables template
├── next.config.js             # Next.js configuration
├── tailwind.config.ts         # Tailwind CSS config
├── tsconfig.json              # TypeScript config
└── package.json               # Dependencies
```

## Environment Variables

Create `.env.local` for local development:

```bash
# Environment
NEXT_PUBLIC_ENV=local

# API URLs
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_WS_URL=ws://localhost:8080

# AWS KVS
NEXT_PUBLIC_KVS_REGION=ap-northeast-2
NEXT_PUBLIC_KVS_CHANNEL_PREFIX=gympt-workout

# Feature Flags
NEXT_PUBLIC_ENABLE_CAMERA=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_DEBUG=false
```

### Environment-specific Configuration

**Local Development:**
```bash
NEXT_PUBLIC_ENV=local
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_WS_URL=ws://localhost:8080
```

**Development (AWS):**
```bash
NEXT_PUBLIC_ENV=dev
NEXT_PUBLIC_API_URL=https://api-dev.gympt.com
NEXT_PUBLIC_WS_URL=wss://api-dev.gympt.com
NEXT_PUBLIC_KVS_REGION=ap-northeast-2
```

**Production:**
```bash
NEXT_PUBLIC_ENV=prod
NEXT_PUBLIC_API_URL=https://api.gympt.com
NEXT_PUBLIC_WS_URL=wss://api.gympt.com
NEXT_PUBLIC_KVS_REGION=ap-northeast-2
```

## Local Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build

```bash
# Local build
npm run build:local

# Development build
npm run build:dev

# Production build
npm run build:prod
```

### Lint & Type Check

```bash
# ESLint
npm run lint

# TypeScript type checking
npm run typecheck
```

## AWS Deployment

### 1. Build for Environment

```bash
# Development
npm run build:dev

# Production
npm run build:prod
```

### 2. Deploy to S3

```bash
# Sync to S3 bucket
aws s3 sync out/ s3://gympt-frontend-prod/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

### 3. CI/CD with GitHub Actions

The repository includes GitHub Actions workflow (`.github/workflows/frontend-deploy.yml`) that:

1. Runs on push to `main` or `develop`
2. Builds with environment-specific variables
3. Syncs to S3
4. Invalidates CloudFront
5. Uses OIDC (no AWS keys needed)

## API Integration

### REST API Client

```typescript
import { apiClient } from '@/lib/api-client';

// Auto-includes JWT token
const response = await apiClient.getCurrentUser();

// Auto-refreshes token on 401
const data = await apiClient.getWorkoutGoal(userId);
```

**Features:**
- Automatic JWT token injection
- Token refresh on 401
- Request/response interceptors
- TypeScript support

### WebSocket Client

```typescript
import { WebSocketClient } from '@/lib/websocket-client';

const ws = new WebSocketClient(accessToken);
await ws.connect(sessionId);

// Listen for posture feedback
ws.on('posture_feedback', (data) => {
  console.log('Feedback:', data);
});

// Send frames
ws.sendPostureFrame(sessionId, exerciseId, frameData);
```

**Features:**
- Auto-reconnect with exponential backoff
- Heartbeat/ping
- Typed message handlers
- Error handling

## WebRTC / KVS Integration

### Architecture

```
Frontend (Browser)
    ↓ WebRTC
AWS Kinesis Video Streams (KVS)
    ↓ Stream Processing
Posture Analysis Service (GPU)
    ↓ WebSocket
Frontend (Real-time Feedback)
```

### KVS WebRTC Client

```typescript
import { KVSWebRTCClient } from '@/lib/kvs-client';

const kvsClient = new KVSWebRTCClient({
  region: 'ap-northeast-2',
  channelName: 'gympt-workout-session-123',
  credentials: {
    accessKeyId: 'ASIA...',
    secretAccessKey: '...',
    sessionToken: '...',
  },
});

// Connect and start streaming
const connection = await kvsClient.connect();

// Get local stream for preview
const localStream = kvsClient.getLocalStream();
videoRef.current.srcObject = localStream;

// Disconnect
await kvsClient.disconnect();
```

### KVS Credentials Flow

1. Frontend requests temporary credentials from backend:
   ```
   GET /api/kvs/credentials/{sessionId}
   ```

2. Backend returns STS credentials:
   ```json
   {
     "accessKeyId": "ASIA...",
     "secretAccessKey": "...",
     "sessionToken": "...",
     "channelName": "gympt-workout-session-123"
   }
   ```

3. Frontend establishes WebRTC connection with KVS

4. Video streams to KVS

5. Backend Lambda ingests from KVS for analysis

### Camera Component Example

```typescript
'use client';

import { useEffect, useRef, useState } from 'react';
import { KVSWebRTCClient } from '@/lib/kvs-client';
import { apiClient } from '@/lib/api-client';

export function CameraWorkout({ sessionId }: { sessionId: string }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [kvsClient, setKvsClient] = useState<KVSWebRTCClient | null>(null);

  useEffect(() => {
    let client: KVSWebRTCClient;

    const init = async () => {
      // Get KVS credentials
      const response = await apiClient.getKVSCredentials(sessionId);
      const { accessKeyId, secretAccessKey, sessionToken, channelName } = 
        response.data;

      // Initialize KVS client
      client = new KVSWebRTCClient({
        region: process.env.NEXT_PUBLIC_KVS_REGION!,
        channelName,
        credentials: { accessKeyId, secretAccessKey, sessionToken },
      });

      // Connect
      await client.connect();
      setKvsClient(client);

      // Show local stream
      const stream = client.getLocalStream();
      if (videoRef.current && stream) {
        videoRef.current.srcObject = stream;
      }
    };

    init().catch(console.error);

    return () => {
      client?.disconnect();
    };
  }, [sessionId]);

  return (
    <div>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full rounded-lg"
      />
    </div>
  );
}
```

## State Management

### Zustand Stores

**Auth Store:**
```typescript
const { user, login, logout, isAuthenticated } = useAuthStore();
```

**Workout Store:**
```typescript
const { 
  currentSession, 
  realtimeFeedback, 
  startSession, 
  completeSession 
} = useWorkoutStore();
```

## Testing

### Unit Tests (Future)

```bash
npm run test
```

### E2E Tests (Future)

```bash
npm run test:e2e
```

## Performance Optimization

- **Code Splitting:** Automatic with Next.js App Router
- **Image Optimization:** Next.js Image component
- **Font Optimization:** next/font
- **Static Generation:** Where possible
- **CDN:** CloudFront for global delivery

## Security

- **JWT Tokens:** Stored in localStorage (consider httpOnly cookies for prod)
- **HTTPS Only:** In production
- **CORS:** Configured on backend
- **Input Validation:** Client-side + server-side
- **XSS Protection:** React's built-in escaping

## Troubleshooting

### WebSocket Connection Fails

```bash
# Check WS URL
echo $NEXT_PUBLIC_WS_URL

# Verify backend is running
curl -I http://localhost:8080/health
```

### KVS WebRTC Connection Fails

1. Check credentials are valid
2. Verify KVS channel exists
3. Check IAM permissions
4. Ensure region is correct

### Token Refresh Loop

- Clear localStorage
- Check backend `/api/auth/refresh` endpoint
- Verify refresh token is not expired

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Note:** WebRTC requires HTTPS in production (except localhost)

## Contributing

1. Create feature branch
2. Make changes
3. Run `npm run typecheck` and `npm run lint`
4. Test thoroughly
5. Create pull request

## License

Proprietary - GymPT Platform Team

---

**Last Updated:** 2024-05-19  
**Version:** 0.1.0 (MVP)  
**Maintainer:** Frontend Team
