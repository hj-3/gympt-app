import { useRef, useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useKVSWebRTC } from '@/hooks/useKVSWebRTC';

interface KVSVideoFeedProps {
  channelName: string;
  sessionId: string;
  onFrame?: (frame: string) => void;
  captureInterval?: number;
}

export function KVSVideoFeed({
  channelName,
  sessionId,
  onFrame,
  captureInterval = 100,
}: KVSVideoFeedProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const frameIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const {
    isConnected,
    isConnecting,
    error: kvsError,
    connect,
    disconnect,
  } = useKVSWebRTC({
    channelName,
    role: 'MASTER',
  });

  // Start camera and KVS connection
  const startCamera = async () => {
    try {
      setError(null);

      // Get media stream
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
        audio: false,
      });

      setStream(mediaStream);

      // Display in video element
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }

      // Connect to KVS
      await connect(mediaStream);

      // Start frame capture
      startFrameCapture();
    } catch (err) {
      console.error('Failed to start camera:', err);
      setError(err instanceof Error ? err.message : 'Failed to access camera');
    }
  };

  // Stop camera and disconnect
  const stopCamera = async () => {
    stopFrameCapture();

    await disconnect();

    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  // Start frame capture for analysis
  const startFrameCapture = () => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
    }

    frameIntervalRef.current = setInterval(() => {
      captureFrame();
    }, captureInterval);
  };

  // Stop frame capture
  const stopFrameCapture = () => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
      frameIntervalRef.current = null;
    }
  };

  // Capture frame from video
  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current || !onFrame) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx || video.readyState !== video.HAVE_ENOUGH_DATA) return;

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to base64 JPEG
    const frameData = canvas.toDataURL('image/jpeg', 0.8);

    // Send to callback
    onFrame(frameData);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  return (
    <Card>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Video Feed (KVS WebRTC)</h3>
          <div className="flex items-center space-x-2">
            {isConnected && (
              <span className="text-xs text-green-600 font-semibold">● Connected</span>
            )}
            {isConnecting && (
              <span className="text-xs text-yellow-600 font-semibold">● Connecting...</span>
            )}
          </div>
        </div>

        {/* Video Display */}
        <div className="relative bg-gray-900 rounded-lg overflow-hidden aspect-video">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />

          {!stream && (
            <div className="absolute inset-0 flex items-center justify-center">
              <p className="text-gray-400">Camera not started</p>
            </div>
          )}

          {/* Session ID Overlay */}
          {stream && (
            <div className="absolute top-2 left-2 bg-black bg-opacity-70 px-2 py-1 rounded text-xs text-white">
              Session: {sessionId.slice(0, 8)}
            </div>
          )}
        </div>

        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Error Display */}
        {(error || kvsError) && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error || kvsError}</p>
          </div>
        )}

        {/* Controls */}
        <div className="flex space-x-2">
          {!stream ? (
            <Button onClick={startCamera} className="w-full">
              Start Camera & Connect to KVS
            </Button>
          ) : (
            <Button onClick={stopCamera} variant="danger" className="w-full">
              Stop Camera
            </Button>
          )}
        </div>

        {/* Connection Info */}
        <div className="text-xs text-gray-500 space-y-1">
          <p>Channel: {channelName}</p>
          <p>Stream via AWS Kinesis Video Streams WebRTC</p>
          {isConnected && <p className="text-green-600">✓ Streaming to KVS</p>}
        </div>
      </div>
    </Card>
  );
}
