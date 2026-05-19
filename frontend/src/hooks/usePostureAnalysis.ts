import { useState, useRef, useCallback } from 'react';

interface PostureAnalysis {
  score: number;
  feedback: string[];
  landmarks: any[];
  timestamp: string;
}

export function usePostureAnalysis() {
  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [analysis, setAnalysis] = useState<PostureAnalysis | null>(null);
  const [repCount, setRepCount] = useState(0);

  const connect = useCallback(async (sessionId?: string) => {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8002';
    const sid = sessionId || Date.now().toString();

    ws.current = new WebSocket(`${wsUrl}/ws/posture/${sid}`);

    ws.current.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'analysis') {
          setAnalysis({
            score: data.score || 0,
            feedback: data.feedback || [],
            landmarks: data.landmarks || [],
            timestamp: new Date().toISOString(),
          });

          if (data.rep_count !== undefined) {
            setRepCount(data.rep_count);
          }
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };
  }, []);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    setIsConnected(false);
    setAnalysis(null);
    setRepCount(0);
  }, []);

  const sendFrame = useCallback((frame: string, exercise: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(
          JSON.stringify({
            type: 'frame',
            frame,
            exercise,
            timestamp: Date.now(),
          })
        );
      } catch (error) {
        console.error('Error sending frame:', error);
      }
    }
  }, []);

  return {
    connect,
    disconnect,
    sendFrame,
    analysis,
    repCount,
    isConnected,
  };
}
