// User Types
export interface User {
  id: string;
  email: string;
  name: string;
  profileImage?: string;
  createdAt: string;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
}

// Body Profile
export interface BodyProfile {
  userId: string;
  height: number;
  weight: number;
  bodyFatPercentage?: number;
  muscleMass?: number;
  skeletalMuscleMass?: number;
  bmi: number;
  measuredAt: string;
}

// Workout Goal
export interface WorkoutGoal {
  userId: string;
  goalType: 'muscle_gain' | 'weight_loss' | 'endurance' | 'flexibility';
  targetWeight?: number;
  targetBodyFat?: number;
  targetDate?: string;
  weeklyWorkouts: number;
  preferredTime: 'morning' | 'afternoon' | 'evening';
}

// Workout Routine
export interface WorkoutExercise {
  exerciseId: string;
  name: string;
  sets: number;
  reps: number;
  duration?: number; // seconds
  restTime: number; // seconds
  intensity: 'low' | 'medium' | 'high';
  videoUrl?: string;
  thumbnailUrl?: string;
}

export interface WorkoutRoutine {
  routineId: string;
  userId: string;
  name: string;
  description: string;
  exercises: WorkoutExercise[];
  totalDuration: number; // minutes
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  focusAreas: string[];
  createdAt: string;
}

// Workout Session
export interface WorkoutSession {
  sessionId: string;
  userId: string;
  routineId: string;
  startTime: string;
  endTime?: string;
  status: 'in_progress' | 'completed' | 'cancelled';
  exercises: SessionExercise[];
  totalCaloriesBurned?: number;
  averageHeartRate?: number;
}

export interface SessionExercise {
  exerciseId: string;
  name: string;
  completedSets: number;
  completedReps: number;
  actualDuration: number;
  postureScore?: number;
  feedback?: PostureFeedback[];
}

// Posture Feedback
export interface PostureFeedback {
  timestamp: string;
  type: 'good' | 'warning' | 'error';
  message: string;
  bodyPart?: string;
  angleDeviation?: number;
}

export interface RealtimeFeedback {
  sessionId: string;
  exerciseId: string;
  timestamp: string;
  postureScore: number;
  feedback: PostureFeedback;
  frame?: string; // base64 image
}

// Workout Report
export interface WorkoutReport {
  reportId: string;
  sessionId: string;
  userId: string;
  completedAt: string;
  summary: {
    totalDuration: number;
    caloriesBurned: number;
    averagePostureScore: number;
    exercisesCompleted: number;
  };
  exerciseDetails: ExerciseReport[];
  insights: string[];
  recommendations: string[];
}

export interface ExerciseReport {
  exerciseId: string;
  name: string;
  sets: number;
  reps: number;
  avgPostureScore: number;
  commonIssues: string[];
  bestSet: number;
}

// Dashboard Statistics
export interface WorkoutStats {
  totalWorkouts: number;
  totalDuration: number; // minutes
  totalCalories: number;
  averagePostureScore: number;
  currentStreak: number;
  longestStreak: number;
  weeklyProgress: WeeklyProgress[];
}

export interface WeeklyProgress {
  week: string;
  workouts: number;
  duration: number;
  calories: number;
}

// WebSocket Message Types
export interface WSMessage {
  type: 'posture_feedback' | 'session_update' | 'error' | 'ping' | 'posture_frame';
  payload: any;
}

// Kinesis Video Streams
export interface KVSConfig {
  region: string;
  channelName: string;
  credentials: {
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken?: string;
  };
}

export interface KVSConnection {
  signalingClient: any;
  peerConnection: RTCPeerConnection;
  dataChannel?: RTCDataChannel;
}

// API Response
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}
