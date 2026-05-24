'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { WebSocketClient } from '@/lib/websocket-client';
import { KVSWebRTCClient } from '@/lib/kvs-client';
import { apiClient } from '@/lib/api-client';
import { getAuthToken } from '@/lib/auth';
import { useWorkoutStore } from '@/lib/store';
import { RealtimeFeedback } from '@/types';
import toast from 'react-hot-toast';

function SessionContent() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('sessionId');
  const videoRef = useRef<HTMLVideoElement>(null);
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);
  const [kvsClient, setKvsClient] = useState<KVSWebRTCClient | null>(null);
  const { currentSession, realtimeFeedback, addFeedback } = useWorkoutStore();
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    if (!sessionId) return;

    let ws: WebSocketClient;
    let kvs: KVSWebRTCClient;

    const init = async () => {
      try {
        // Get KVS credentials
        const credsRes = await apiClient.getKVSCredentials(sessionId);
        const { accessKeyId, secretAccessKey, sessionToken, channelName } = credsRes.data;

        // Initialize KVS WebRTC
        kvs = new KVSWebRTCClient({
          region: process.env.NEXT_PUBLIC_KVS_REGION!,
          channelName,
          credentials: { accessKeyId, secretAccessKey, sessionToken },
        });

        await kvs.connect();
        setKvsClient(kvs);

        // Show local stream
        const stream = kvs.getLocalStream();
        if (videoRef.current && stream) {
          videoRef.current.srcObject = stream;
        }

        setIsStreaming(true);

        // Initialize WebSocket for feedback
        const token = await getAuthToken();
        if (token) {
          ws = new WebSocketClient(token);
          await ws.connect(sessionId);
          setWsClient(ws);

          // Listen for posture feedback
          ws.on('posture_feedback', (feedback: RealtimeFeedback) => {
            addFeedback(feedback);
          });
        }
      } catch (error) {
        console.error('Failed to initialize session:', error);
        toast.error('Failed to start camera');
      }
    };

    init();

    return () => {
      kvs?.disconnect();
      ws?.disconnect();
    };
  }, [sessionId, addFeedback]);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Feed */}
          <div className="lg:col-span-2">
            <div className="bg-black rounded-lg overflow-hidden aspect-video">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
            </div>
            <div className="mt-4 flex justify-center gap-4">
              <button
                disabled={!isStreaming}
                className="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                End Workout
              </button>
            </div>
          </div>

          {/* Feedback Panel */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-bold mb-4">Real-time Feedback</h2>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {realtimeFeedback.map((feedback, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg ${
                    feedback.feedback.type === 'good'
                      ? 'bg-green-900'
                      : feedback.feedback.type === 'warning'
                      ? 'bg-yellow-900'
                      : 'bg-red-900'
                  }`}
                >
                  <p className="text-sm font-medium">{feedback.feedback.message}</p>
                  <p className="text-xs text-gray-300 mt-1">
                    Score: {feedback.postureScore.toFixed(1)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SessionPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading session...</div>}>
      <SessionContent />
    </Suspense>
  );
}
