import { useState, useRef, useCallback, useEffect } from 'react';

export interface PostureAnalysis {
  formScore: number;
  isValid: boolean;
  feedback: string[];
  angles: Record<string, number>;
  timestamp: string;
  repCount: number;
}

export interface Landmark {
  x: number;
  y: number;
  z?: number;
  visibility?: number;
}

const POSTURE_WS_URL = process.env.NEXT_PUBLIC_POSTURE_WS_URL || 'ws://localhost:8002';

/**
 * Real-time posture analysis driven entirely by the posture-analysis-service.
 *
 * All pose landmarks, scores, joint angles, feedback and rep counts come from
 * the server's MediaPipe pipeline over WebSocket. There is no client-side
 * simulation or fallback — if the socket is unavailable the session is simply
 * marked disconnected.
 */
export function usePostureAnalysis() {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [analysis, setAnalysis] = useState<PostureAnalysis | null>(null);
  const [repCount, setRepCount] = useState(0);
  const [landmarks, setLandmarks] = useState<Landmark[]>([]);
  const [poseDetected, setPoseDetected] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const exerciseRef = useRef<string>('squat');
  const sessionStartRef = useRef<number>(0);

  const connect = useCallback(async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setRepCount(0);
    setAnalysis(null);
    setLandmarks([]);
    setPoseDetected(false);
    sessionStartRef.current = Date.now();

    return new Promise<void>((resolve, reject) => {
      try {
        const ws = new WebSocket(`${POSTURE_WS_URL}/ws/posture/${sessionId}`);
        wsRef.current = ws;

        ws.onopen = () => {
          setIsConnected(true);
          console.log('Posture WebSocket connected');
          resolve();
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type !== 'analysis') return;

            // Skeleton: use real landmarks from the server
            if (Array.isArray(data.landmarks)) {
              setLandmarks(data.landmarks as Landmark[]);
            }

            setPoseDetected(Boolean(data.pose_detected));

            // Score is 0-10 from the rules engine -> scale to 0-100 for UI
            const score = Math.min((data.score || 0) * 10, 100);

            // Feedback messages come from the server feedback service
            const fb = data.feedback || {};
            const msgs: string[] = [];
            if (fb.overall) msgs.push(fb.overall);
            (fb.corrections || []).forEach((c: any) => {
              if (c.correction) msgs.push(c.correction);
            });

            setAnalysis({
              formScore: score,
              isValid: Boolean(data.pose_detected) && score >= 70,
              feedback: msgs,
              angles: data.angles || {},
              timestamp: fb.timestamp || new Date().toISOString(),
              repCount: data.rep_count ?? 0,
            });

            if (typeof data.rep_count === 'number') {
              setRepCount(data.rep_count);
            }
          } catch (e) {
            console.error('WS parse error:', e);
          }
        };

        ws.onerror = (err) => {
          console.error('Posture WebSocket error:', err);
          setIsConnected(false);
          reject(err);
        };

        ws.onclose = () => {
          setIsConnected(false);
        };
      } catch (err) {
        setIsConnected(false);
        reject(err);
      }
    });
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setAnalysis(null);
    setLandmarks([]);
    setPoseDetected(false);
    setRepCount(0);
    setCurrentSessionId(null);
  }, []);

  const sendFrame = useCallback((frame: string, exercise: string) => {
    exerciseRef.current = exercise;
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      const base64 = frame.startsWith('data:') ? frame.split(',')[1] : frame;
      ws.send(JSON.stringify({ type: 'frame', frame: base64, exercise }));
    }
  }, []);

  const getSessionDuration = useCallback(() => {
    return Math.round((Date.now() - sessionStartRef.current) / 60000);
  }, []);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return {
    connect,
    disconnect,
    sendFrame,
    analysis,
    landmarks,
    repCount,
    isConnected,
    poseDetected,
    sessionId: currentSessionId,
    getSessionDuration,
  };
}
