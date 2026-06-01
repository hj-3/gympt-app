'use client';

import { useRef, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { PoseCanvas } from './PoseCanvas';
import type { Landmark } from '@/hooks/usePostureAnalysis';

interface VideoFeedProps {
  isActive: boolean;
  onFrame?: (frame: string) => void;
  exercise: string;
  landmarks?: Landmark[];
}

export function VideoFeed({ isActive, onFrame, exercise, landmarks = [] }: VideoFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [videoDimensions, setVideoDimensions] = useState({ width: 640, height: 360 });

  useEffect(() => {
    let stream: MediaStream | null = null;
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 },
          audio: false,
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = () => {
            if (videoRef.current) {
              setVideoDimensions({
                width: videoRef.current.videoWidth || 640,
                height: videoRef.current.videoHeight || 360,
              });
            }
          };
        }

        if (onFrame && isActive) {
          intervalId = setInterval(() => {
            captureFrame();
          }, 200); // 5 FPS — enough for posture analysis
        }

        setError(null);
      } catch (err) {
        console.error('Camera error:', err);
        setError('카메라 접근에 실패했습니다. 권한을 확인해주세요.');
      }
    };

    const captureFrame = () => {
      if (videoRef.current && canvasRef.current) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        if (ctx && video.readyState === video.HAVE_ENOUGH_DATA) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          ctx.drawImage(video, 0, 0);

          const frameData = canvas.toDataURL('image/jpeg', 0.7);
          if (onFrame) onFrame(frameData);
        }
      }
    };

    if (isActive) startCamera();

    return () => {
      if (intervalId) clearInterval(intervalId);
      if (stream) stream.getTracks().forEach((track) => track.stop());
    };
  }, [isActive, onFrame]);

  const exerciseLabels: Record<string, string> = {
    squat: '스쿼트',
    pushup: '푸시업',
    lunge: '런지',
    plank: '플랭크',
  };

  return (
    <Card padding="none">
      <div className="relative aspect-video bg-gray-900 rounded-lg overflow-hidden">
        {error ? (
          <div className="absolute inset-0 flex items-center justify-center text-white">
            <div className="text-center px-4">
              <p className="mb-2">{error}</p>
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

            {/* Hidden canvas for frame capture */}
            <canvas ref={canvasRef} className="hidden" />

            {isActive && (
              <div className="absolute top-4 left-4 bg-red-600 text-white px-3 py-1 rounded-full text-sm font-semibold flex items-center space-x-2">
                <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
                <span>REC</span>
              </div>
            )}

            <div className="absolute top-4 right-4 bg-black bg-opacity-60 text-white px-3 py-1 rounded-lg text-sm">
              {exerciseLabels[exercise] || exercise}
            </div>

            {/* AI analysis badge */}
            {isActive && landmarks.length > 0 && (
              <div className="absolute bottom-4 left-4 bg-blue-600 bg-opacity-80 text-white px-3 py-1 rounded-lg text-xs font-medium flex items-center gap-1">
                <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                AI 자세 분석 중
              </div>
            )}
          </>
        )}
      </div>
    </Card>
  );
}
