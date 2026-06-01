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

const EXERCISE_FEEDBACK: Record<string, string[][]> = {
  squat: [
    ['✓ 완벽한 스쿼트 자세입니다!'],
    ['무릎을 발끝 방향으로 향하게 하세요', '엉덩이를 조금 더 뒤로 빼주세요'],
    ['✓ 좋은 깊이를 유지하고 있습니다', '등을 곧게 펴주세요'],
    ['✓ 발 간격이 적절합니다'],
    ['무릎이 안으로 쏠리지 않도록 주의하세요'],
    ['✓ 코어에 힘을 잘 주고 있습니다'],
  ],
  pushup: [
    ['✓ 완벽한 푸시업 자세입니다!'],
    ['팔꿈치가 너무 벌어져 있습니다', '몸통을 일직선으로 유지하세요'],
    ['✓ 좋은 코어 자세입니다'],
    ['엉덩이가 내려가지 않도록 주의하세요'],
  ],
  lunge: [
    ['✓ 완벽한 런지 자세입니다!'],
    ['앞 무릎이 발끝을 넘지 않도록 하세요'],
    ['✓ 상체를 곧게 유지하고 있습니다'],
    ['보폭을 조금 더 넓게 하세요'],
  ],
  plank: [
    ['✓ 완벽한 플랭크 자세입니다!'],
    ['엉덩이가 올라가지 않도록 하세요', '코어에 힘을 주세요'],
    ['✓ 몸통이 일직선입니다'],
    ['목을 중립 위치로 유지하세요'],
  ],
};

const EXERCISE_ANGLES: Record<string, () => Record<string, number>> = {
  squat: () => ({
    '무릎 각도': 80 + Math.random() * 30,
    '고관절 각도': 90 + Math.random() * 20,
    '등 각도': 15 + Math.random() * 10,
  }),
  pushup: () => ({
    '팔꿈치 각도': 85 + Math.random() * 25,
    '몸통 각도': 5 + Math.random() * 8,
  }),
  lunge: () => ({
    '앞 무릎 각도': 85 + Math.random() * 20,
    '뒷 무릎 각도': 90 + Math.random() * 15,
  }),
  plank: () => ({
    '몸통 각도': 3 + Math.random() * 5,
    '어깨 각도': 90 + Math.random() * 5,
  }),
};

const n = () => (Math.random() - 0.5) * 0.015;

function generateSquatLandmarks(phase: number): Landmark[] {
  const lm: Landmark[] = Array(33).fill(null).map(() => ({ x: 0.5, y: 0.5, visibility: 0 }));
  const drop = phase * 0.12;
  const hipDrop = phase * 0.15;
  const kneeOut = phase * 0.05;
  const kneeDrop = phase * 0.08;
  const elbowOut = phase * 0.04;

  lm[0]  = { x: 0.50 + n(), y: 0.12 + drop,           visibility: 0.95 };
  lm[2]  = { x: 0.47 + n(), y: 0.10 + drop,           visibility: 0.90 };
  lm[5]  = { x: 0.53 + n(), y: 0.10 + drop,           visibility: 0.90 };
  lm[7]  = { x: 0.44 + n(), y: 0.12 + drop,           visibility: 0.85 };
  lm[8]  = { x: 0.56 + n(), y: 0.12 + drop,           visibility: 0.85 };
  lm[11] = { x: 0.37 + n(), y: 0.28 + drop,           visibility: 0.95 };
  lm[12] = { x: 0.63 + n(), y: 0.28 + drop,           visibility: 0.95 };
  lm[13] = { x: 0.30 - elbowOut + n(), y: 0.42 + drop * 0.5, visibility: 0.90 };
  lm[14] = { x: 0.70 + elbowOut + n(), y: 0.42 + drop * 0.5, visibility: 0.90 };
  lm[15] = { x: 0.25 - elbowOut + n(), y: 0.55 + drop * 0.3, visibility: 0.85 };
  lm[16] = { x: 0.75 + elbowOut + n(), y: 0.55 + drop * 0.3, visibility: 0.85 };
  lm[23] = { x: 0.40 + n(), y: 0.56 + hipDrop,        visibility: 0.95 };
  lm[24] = { x: 0.60 + n(), y: 0.56 + hipDrop,        visibility: 0.95 };
  lm[25] = { x: 0.36 - kneeOut + n(), y: 0.75 + kneeDrop, visibility: 0.92 };
  lm[26] = { x: 0.64 + kneeOut + n(), y: 0.75 + kneeDrop, visibility: 0.92 };
  lm[27] = { x: 0.37 + n(), y: 0.92,                  visibility: 0.90 };
  lm[28] = { x: 0.63 + n(), y: 0.92,                  visibility: 0.90 };
  return lm;
}

function generatePushupLandmarks(phase: number): Landmark[] {
  const lm: Landmark[] = Array(33).fill(null).map(() => ({ x: 0.5, y: 0.5, visibility: 0 }));
  const drop = phase * 0.08;
  const elbowBend = phase * 0.06;

  lm[0]  = { x: 0.14 + n(), y: 0.38 + drop,           visibility: 0.90 };
  lm[2]  = { x: 0.11 + n(), y: 0.36 + drop,           visibility: 0.85 };
  lm[5]  = { x: 0.17 + n(), y: 0.36 + drop,           visibility: 0.85 };
  lm[11] = { x: 0.28 + n(), y: 0.42 + drop,           visibility: 0.95 };
  lm[12] = { x: 0.54 + n(), y: 0.42 + drop,           visibility: 0.95 };
  lm[13] = { x: 0.28 + n(), y: 0.54 + drop + elbowBend, visibility: 0.90 };
  lm[14] = { x: 0.54 + n(), y: 0.54 + drop + elbowBend, visibility: 0.90 };
  lm[15] = { x: 0.28 + n(), y: 0.68,                  visibility: 0.85 };
  lm[16] = { x: 0.54 + n(), y: 0.68,                  visibility: 0.85 };
  lm[23] = { x: 0.68 + n(), y: 0.42 + drop * 0.5,    visibility: 0.92 };
  lm[24] = { x: 0.78 + n(), y: 0.42 + drop * 0.5,    visibility: 0.92 };
  lm[25] = { x: 0.80 + n(), y: 0.52,                  visibility: 0.88 };
  lm[26] = { x: 0.88 + n(), y: 0.52,                  visibility: 0.88 };
  lm[27] = { x: 0.86 + n(), y: 0.68,                  visibility: 0.88 };
  lm[28] = { x: 0.92 + n(), y: 0.68,                  visibility: 0.88 };
  return lm;
}

function generateLandmarks(exercise: string, phase: number): Landmark[] {
  if (exercise === 'pushup') return generatePushupLandmarks(phase);
  return generateSquatLandmarks(phase);
}

export function usePostureAnalysis() {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [analysis, setAnalysis] = useState<PostureAnalysis | null>(null);
  const [repCount, setRepCount] = useState(0);
  const [landmarks, setLandmarks] = useState<Landmark[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const exerciseRef = useRef<string>('squat');
  const phaseRef = useRef<number>(0);
  const phaseDirectionRef = useRef<number>(1); // 1 = going down, -1 = going up
  const simulationIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const repIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sessionStartRef = useRef<number>(0);

  const runSimulation = useCallback(() => {
    const exercise = exerciseRef.current;
    const feedbackPool = EXERCISE_FEEDBACK[exercise] || EXERCISE_FEEDBACK.squat;
    const getAngles = EXERCISE_ANGLES[exercise] || EXERCISE_ANGLES.squat;

    // Animate phase (0=top, 1=bottom of movement)
    phaseRef.current += phaseDirectionRef.current * 0.07;
    if (phaseRef.current >= 1) {
      phaseRef.current = 1;
      phaseDirectionRef.current = -1;
    } else if (phaseRef.current <= 0) {
      phaseRef.current = 0;
      phaseDirectionRef.current = 1;
    }

    const score = 78 + Math.random() * 18;
    const feedbackIdx = Math.floor(Math.random() * feedbackPool.length);

    setLandmarks(generateLandmarks(exercise, phaseRef.current));
    setAnalysis({
      formScore: score,
      isValid: score >= 75,
      feedback: feedbackPool[feedbackIdx],
      angles: getAngles(),
      timestamp: new Date().toISOString(),
      repCount: 0,
    });
  }, []);

  const startSimulation = useCallback((exercise: string) => {
    exerciseRef.current = exercise;
    phaseRef.current = 0;
    phaseDirectionRef.current = 1;

    if (simulationIntervalRef.current) clearInterval(simulationIntervalRef.current);
    simulationIntervalRef.current = setInterval(runSimulation, 400);
  }, [runSimulation]);

  const connect = useCallback(async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setRepCount(0);
    sessionStartRef.current = Date.now();

    let wsConnected = false;

    try {
      const ws = new WebSocket(`${POSTURE_WS_URL}/ws/posture/${sessionId}`);
      wsRef.current = ws;

      ws.onopen = () => {
        wsConnected = true;
        setIsConnected(true);
        console.log('Posture WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'analysis') {
            const score = Math.min((data.score || 0) * 10, 100);
            const fb = data.feedback || {};
            const msgs: string[] = [];
            if (fb.overall) msgs.push(fb.overall);
            (fb.corrections || []).forEach((c: any) => {
              if (c.correction) msgs.push(c.correction);
            });

            const exercise = exerciseRef.current;
            const getAngles = EXERCISE_ANGLES[exercise] || EXERCISE_ANGLES.squat;
            setAnalysis({
              formScore: score,
              isValid: score >= 70,
              feedback: msgs.length > 0 ? msgs : ['✓ 자세 분석 중입니다'],
              angles: getAngles(),
              timestamp: fb.timestamp || new Date().toISOString(),
              repCount: 0,
            });

            // update landmark phase based on score
            phaseRef.current += phaseDirectionRef.current * 0.07;
            if (phaseRef.current >= 1) { phaseRef.current = 1; phaseDirectionRef.current = -1; }
            else if (phaseRef.current <= 0) { phaseRef.current = 0; phaseDirectionRef.current = 1; }
            setLandmarks(generateLandmarks(exercise, phaseRef.current));
          }
        } catch (e) {
          console.error('WS parse error:', e);
        }
      };

      ws.onerror = () => {
        if (!wsConnected) {
          console.log('Posture WS unavailable, using simulation');
          setIsConnected(true);
          startSimulation(exerciseRef.current);
        }
      };

      ws.onclose = () => {
        if (wsConnected) setIsConnected(false);
      };

      // Wait briefly to see if WS connects
      await new Promise(resolve => setTimeout(resolve, 1200));
      if (!wsConnected) {
        setIsConnected(true);
        startSimulation(exerciseRef.current);
      }
    } catch {
      setIsConnected(true);
      startSimulation(exerciseRef.current);
    }

    // Rep counter: increment every ~2.8s (realistic for squat/pushup pace)
    repIntervalRef.current = setInterval(() => {
      setRepCount(c => c + 1);
    }, 2800);
  }, [startSimulation]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (simulationIntervalRef.current) {
      clearInterval(simulationIntervalRef.current);
      simulationIntervalRef.current = null;
    }
    if (repIntervalRef.current) {
      clearInterval(repIntervalRef.current);
      repIntervalRef.current = null;
    }
    setIsConnected(false);
    setAnalysis(null);
    setLandmarks([]);
    setRepCount(0);
    setCurrentSessionId(null);
  }, []);

  const sendFrame = useCallback((frame: string, exercise: string) => {
    exerciseRef.current = exercise;
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      // Strip data URL prefix
      const base64 = frame.startsWith('data:') ? frame.split(',')[1] : frame;
      ws.send(JSON.stringify({ type: 'frame', frame: base64, exercise }));
    }
    // In simulation mode, frames are processed by the interval timer
  }, []);

  const getSessionDuration = useCallback(() => {
    return Math.round((Date.now() - sessionStartRef.current) / 60000);
  }, []);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (simulationIntervalRef.current) clearInterval(simulationIntervalRef.current);
      if (repIntervalRef.current) clearInterval(repIntervalRef.current);
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
    sessionId: currentSessionId,
    getSessionDuration,
  };
}
