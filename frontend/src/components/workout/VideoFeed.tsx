'use client';

import { useRef, useEffect, useState } from 'react';
import { PoseCanvas } from './PoseCanvas';
import type { Landmark } from '@/hooks/usePostureAnalysis';

interface VideoFeedProps {
  isActive: boolean;
  onFrame?: (frame: string) => void;
  exercise: string;
  landmarks?: Landmark[];
}

const CAMERA_GUIDE: Record<string, { angle: string; tip: string; color: string }> = {
  squat:  { angle: '측면', tip: '카메라를 몸의 옆에서 비춰주세요 (무릎·고관절 각도 측정)', color: 'bg-yellow-500' },
  pushup: { angle: '측면', tip: '카메라를 몸의 옆에서 비춰주세요 (팔꿈치·몸통 정렬 측정)', color: 'bg-yellow-500' },
  lunge:  { angle: '측면', tip: '카메라를 몸의 옆에서 비춰주세요 (무릎 각도 측정)',       color: 'bg-yellow-500' },
  plank:  { angle: '측면', tip: '카메라를 몸의 옆에서 비춰주세요 (몸통 일직선 측정)',      color: 'bg-yellow-500' },
};

const EXERCISE_LABELS: Record<string, string> = {
  squat: '스쿼트',
  pushup: '푸시업',
  lunge: '런지',
  plank: '플랭크',
};

export function VideoFeed({ isActive, onFrame, exercise, landmarks = [] }: VideoFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [videoDimensions, setVideoDimensions] = useState({ width: 1280, height: 720 });
  const [guideVisible, setGuideVisible] = useState(true);

  const onFrameRef = useRef(onFrame);
  useEffect(() => { onFrameRef.current = onFrame; });

  useEffect(() => {
    let stream: MediaStream | null = null;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const captureFrame = () => {
      if (videoRef.current && canvasRef.current) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (ctx && video.readyState === video.HAVE_ENOUGH_DATA) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          ctx.drawImage(video, 0, 0);
          const frameData = canvas.toDataURL('image/jpeg', 0.75);
          if (onFrameRef.current) onFrameRef.current(frameData);
        }
      }
    };

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
          audio: false,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = () => {
            if (videoRef.current) {
              setVideoDimensions({
                width: videoRef.current.videoWidth || 1280,
                height: videoRef.current.videoHeight || 720,
              });
            }
          };
        }
        if (isActive) intervalId = setInterval(captureFrame, 200); // 5 FPS
        setError(null);
      } catch (err) {
        console.error('Camera error:', err);
        setError('카메라 접근에 실패했습니다. 권한을 확인해주세요.');
      }
    };

    if (isActive) startCamera();

    return () => {
      if (intervalId) clearInterval(intervalId);
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, [isActive]);

  // Auto-hide guide after 8 seconds of active session
  useEffect(() => {
    if (!isActive) return;
    setGuideVisible(true);
    const t = setTimeout(() => setGuideVisible(false), 8000);
    return () => clearTimeout(t);
  }, [isActive, exercise]);

  const guide = CAMERA_GUIDE[exercise];

  return (
    <div className="w-full">
      {/* Camera direction guide banner */}
      {guide && guideVisible && isActive && (
        <div className={`${guide.color} text-white text-sm font-medium px-4 py-2.5 rounded-t-2xl flex items-center justify-between`}>
          <div className="flex items-center gap-2">
            <span className="text-lg">📷</span>
            <span>
              <span className="font-bold">[{guide.angle}]</span> {guide.tip}
            </span>
          </div>
          <button onClick={() => setGuideVisible(false)} className="text-white/70 hover:text-white text-lg leading-none">×</button>
        </div>
      )}

      {/* Video area — taller aspect ratio for better body visibility */}
      <div className={`relative bg-gray-900 overflow-hidden ${guide && guideVisible && isActive ? 'rounded-b-2xl' : 'rounded-2xl'}`}
           style={{ aspectRatio: '4/3' }}>
        {error ? (
          <div className="absolute inset-0 flex items-center justify-center text-white">
            <div className="text-center px-4">
              <div className="text-5xl mb-3">📷</div>
              <p className="font-medium mb-1">{error}</p>
              <p className="text-sm text-gray-400">브라우저 카메라 권한을 허용해주세요</p>
            </div>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />

            {/* Skeleton overlay */}
            {isActive && landmarks.length > 0 && (
              <div className="absolute inset-0 pointer-events-none">
                <PoseCanvas
                  landmarks={landmarks}
                  width={videoDimensions.width}
                  height={videoDimensions.height}
                  className="w-full h-full"
                />
              </div>
            )}

            <canvas ref={canvasRef} className="hidden" />

            {isActive && (
              <div className="absolute top-3 left-3 bg-red-600 text-white px-2.5 py-1 rounded-full text-xs font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
                REC
              </div>
            )}

            <div className="absolute top-3 right-3 bg-black/60 text-white px-3 py-1 rounded-lg text-sm font-medium">
              {EXERCISE_LABELS[exercise] || exercise}
            </div>

            {/* Camera angle reminder (small, always visible) */}
            {guide && isActive && (
              <div
                onClick={() => setGuideVisible(!guideVisible)}
                className="absolute bottom-3 right-3 bg-yellow-500/90 text-white px-2.5 py-1 rounded-lg text-xs font-bold cursor-pointer hover:bg-yellow-400 transition-colors"
              >
                {guide.angle} 촬영
              </div>
            )}

            {isActive && landmarks.length > 0 && (
              <div className="absolute bottom-3 left-3 bg-blue-600/80 text-white px-2.5 py-1 rounded-lg text-xs font-medium flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                AI 자세 분석 중
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
