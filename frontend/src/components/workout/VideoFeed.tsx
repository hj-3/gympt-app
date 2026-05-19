'use client';

import { useRef, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';

interface VideoFeedProps {
  isActive: boolean;
  onFrame?: (frame: string) => void;
  exercise: string;
}

export function VideoFeed({ isActive, onFrame, exercise }: VideoFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stream: MediaStream | null = null;
    let intervalId: NodeJS.Timeout | null = null;

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 },
          audio: false,
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }

        // Send frames to backend
        if (onFrame && isActive) {
          intervalId = setInterval(() => {
            captureFrame();
          }, 100); // 10 FPS
        }

        setError(null);
      } catch (err) {
        console.error('Camera error:', err);
        setError('Failed to access camera. Please check permissions.');
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

          const frameData = canvas.toDataURL('image/jpeg', 0.8);
          if (onFrame) {
            onFrame(frameData);
          }
        }
      }
    };

    if (isActive) {
      startCamera();
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [isActive, onFrame]);

  return (
    <Card padding="none">
      <div className="relative aspect-video bg-gray-900 rounded-lg overflow-hidden">
        {error ? (
          <div className="absolute inset-0 flex items-center justify-center text-white">
            <div className="text-center">
              <p className="mb-2">{error}</p>
              <p className="text-sm text-gray-400">
                Make sure your browser has camera permissions enabled
              </p>
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
            <canvas ref={canvasRef} className="hidden" />

            {isActive && (
              <div className="absolute top-4 left-4 bg-red-600 text-white px-3 py-1 rounded-full text-sm font-semibold flex items-center space-x-2">
                <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                <span>Recording</span>
              </div>
            )}

            <div className="absolute top-4 right-4 bg-black bg-opacity-60 text-white px-3 py-1 rounded-lg text-sm">
              Exercise: {exercise}
            </div>
          </>
        )}
      </div>
    </Card>
  );
}
