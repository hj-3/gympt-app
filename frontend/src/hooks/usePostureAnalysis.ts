import { useState, useRef, useCallback, useEffect } from 'react';
import SockJS from 'sockjs-client';
import { Client } from '@stomp/stompjs';

interface PostureAnalysis {
  formScore: number;
  isValid: boolean;
  feedback: string[];
  angles: Record<string, number>;
  timestamp: string;
  repCount: number;
}

export function usePostureAnalysis() {
  const stompClient = useRef<Client | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [analysis, setAnalysis] = useState<PostureAnalysis | null>(null);
  const [repCount, setRepCount] = useState(0);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const connect = useCallback(async (sessionId: string) => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8080';

    // Create STOMP client over SockJS
    const client = new Client({
      webSocketFactory: () => new SockJS(`${wsUrl}/ws`),
      debug: (str) => {
        console.log('STOMP Debug:', str);
      },
      reconnectDelay: 5000,
      heartbeatIncoming: 4000,
      heartbeatOutgoing: 4000,
    });

    client.onConnect = () => {
      console.log('STOMP Connected to session:', sessionId);
      setIsConnected(true);
      setCurrentSessionId(sessionId);

      // Subscribe to session-specific topic
      client.subscribe(`/topic/workout/${sessionId}`, (message) => {
        try {
          const data = JSON.parse(message.body);
          console.log('Received posture feedback:', data);

          setAnalysis({
            formScore: data.formScore || 0,
            isValid: data.isValid || false,
            feedback: data.feedback || [],
            angles: data.angles || {},
            timestamp: data.timestamp || new Date().toISOString(),
            repCount: data.repCount || 0,
          });

          if (data.repCount !== undefined) {
            setRepCount(data.repCount);
          }
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      });

      // Send subscription message
      client.publish({
        destination: `/app/workout/subscribe/${sessionId}`,
        body: JSON.stringify({ sessionId }),
      });
    };

    client.onStompError = (frame) => {
      console.error('STOMP Error:', frame.headers['message']);
      console.error('Details:', frame.body);
      setIsConnected(false);
    };

    client.onWebSocketClose = () => {
      console.log('WebSocket connection closed');
      setIsConnected(false);
    };

    client.activate();
    stompClient.current = client;
  }, []);

  const disconnect = useCallback(() => {
    if (stompClient.current) {
      stompClient.current.deactivate();
      stompClient.current = null;
    }
    setIsConnected(false);
    setAnalysis(null);
    setRepCount(0);
    setCurrentSessionId(null);
  }, []);

  // This is now just a stub - actual frame analysis happens via REST API
  const sendFrame = useCallback((frame: string, exercise: string) => {
    // Frames are sent via REST API to posture-analysis-service
    // which then pushes results to WebSocket
    console.log('Frame capture - to be sent via REST API');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (stompClient.current) {
        stompClient.current.deactivate();
      }
    };
  }, []);

  return {
    connect,
    disconnect,
    sendFrame,
    analysis,
    repCount,
    isConnected,
    sessionId: currentSessionId,
  };
}
