import { useState, useRef, useCallback, useEffect } from 'react';
import { KVSWebRTCClient } from '@/lib/kvs-webrtc';
import { useAuthStore } from '@/lib/store';

interface UseKVSWebRTCOptions {
  channelName: string;
  region?: string;
  role?: 'MASTER' | 'VIEWER';
}

export function useKVSWebRTC(options: UseKVSWebRTCOptions) {
  const { user } = useAuthStore();
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null);

  const clientRef = useRef<KVSWebRTCClient | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);

  const connect = useCallback(async (localStream: MediaStream) => {
    if (!user) {
      setError('User not authenticated');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      // Get AWS credentials from Cognito
      // In production, this should use AWS Amplify to get temporary credentials
      const credentials = {
        accessKeyId: process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID || '',
        secretAccessKey: process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY || '',
        sessionToken: process.env.NEXT_PUBLIC_AWS_SESSION_TOKEN,
      };

      const client = new KVSWebRTCClient({
        region: options.region || process.env.NEXT_PUBLIC_AWS_REGION || 'ap-northeast-2',
        channelName: options.channelName,
        clientId: user.userId,
        role: options.role || 'MASTER',
        credentials,
      });

      await client.connect(localStream);

      clientRef.current = client;
      localStreamRef.current = localStream;
      setIsConnected(true);
      setIsConnecting(false);

      // Poll for remote stream
      const checkRemoteStream = setInterval(() => {
        const stream = client.getRemoteStream();
        if (stream) {
          setRemoteStream(stream);
          clearInterval(checkRemoteStream);
        }
      }, 500);

      // Clean up interval after 30 seconds
      setTimeout(() => clearInterval(checkRemoteStream), 30000);
    } catch (err) {
      console.error('Failed to connect to KVS WebRTC:', err);
      setError(err instanceof Error ? err.message : 'Connection failed');
      setIsConnecting(false);
      setIsConnected(false);
    }
  }, [user, options]);

  const disconnect = useCallback(async () => {
    if (clientRef.current) {
      await clientRef.current.disconnect();
      clientRef.current = null;
    }

    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
      localStreamRef.current = null;
    }

    setIsConnected(false);
    setRemoteStream(null);
    setError(null);
  }, []);

  const sendData = useCallback((data: string) => {
    if (clientRef.current) {
      clientRef.current.sendData(data);
    }
  }, []);

  const getConnectionState = useCallback(() => {
    return clientRef.current?.getConnectionState() || null;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (clientRef.current) {
        clientRef.current.disconnect();
      }
      if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return {
    isConnected,
    isConnecting,
    error,
    remoteStream,
    connect,
    disconnect,
    sendData,
    getConnectionState,
  };
}
