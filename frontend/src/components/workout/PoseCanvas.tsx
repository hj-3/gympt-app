'use client';

import { useEffect, useRef } from 'react';

export interface Landmark {
  x: number;
  y: number;
  z?: number;
  visibility?: number;
}

export interface PoseCanvasProps {
  landmarks: Landmark[];
  width: number;
  height: number;
  className?: string;
}

// MediaPipe Pose landmark connections
const POSE_CONNECTIONS = [
  [11, 12], // shoulders
  [11, 13], // left shoulder to elbow
  [13, 15], // left elbow to wrist
  [12, 14], // right shoulder to elbow
  [14, 16], // right elbow to wrist
  [11, 23], // left shoulder to hip
  [12, 24], // right shoulder to hip
  [23, 24], // hips
  [23, 25], // left hip to knee
  [25, 27], // left knee to ankle
  [24, 26], // right hip to knee
  [26, 28], // right knee to ankle
];

export function PoseCanvas({ landmarks, width, height, className = '' }: PoseCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !landmarks || landmarks.length === 0) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw connections (skeleton lines)
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 3;
    POSE_CONNECTIONS.forEach(([start, end]) => {
      const startPoint = landmarks[start];
      const endPoint = landmarks[end];

      if (startPoint && endPoint) {
        // Only draw if both points have good visibility
        if (
          (startPoint.visibility ?? 1) > 0.5 &&
          (endPoint.visibility ?? 1) > 0.5
        ) {
          ctx.beginPath();
          ctx.moveTo(startPoint.x * width, startPoint.y * height);
          ctx.lineTo(endPoint.x * width, endPoint.y * height);
          ctx.stroke();
        }
      }
    });

    // Draw landmarks (joints)
    landmarks.forEach((landmark) => {
      if ((landmark.visibility ?? 1) > 0.5) {
        ctx.fillStyle = '#ff0000';
        ctx.beginPath();
        ctx.arc(
          landmark.x * width,
          landmark.y * height,
          5,
          0,
          2 * Math.PI
        );
        ctx.fill();
      }
    });
  }, [landmarks, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      className={className}
    />
  );
}
