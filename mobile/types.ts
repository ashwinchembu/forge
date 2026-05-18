/** TypeScript types matching Forge API responses — use in React Native / Expo */

export interface ExerciseComparison {
  exercise: string;
  target_weight: number;
  actual_weight?: number;
  target_reps: string;
  actual_reps?: number[];
  status: "hit" | "close" | "missed" | "no_data";
  volume_delta_pct?: number;
}

export interface DailyAnalysis {
  date: string;
  week: number;
  phase: string;
  expected_workout: string | null;
  score: number;
  workout?: {
    exercises: ExerciseComparison[];
    hit_rate: number;
  };
  nutrition?: {
    calories: number;
    target_calories: number;
    protein_g: number;
    target_protein_g: number;
    carbs_g: number;
    fat_g: number;
    calorie_delta: number;
    protein_delta: number;
  };
  recovery?: {
    sleep_hours?: number;
    hrv_ms?: number;
    resting_heart_rate?: number;
    steps?: number;
  };
  recommendations: string[];
}

export interface Workout {
  _id: string;
  date: string;
  name: string;
  duration_minutes?: number;
  exercises: Array<{
    name: string;
    sets: Array<{ set_number: number; weight_lbs: number; reps: number }>;
  }>;
  total_volume_lbs?: number;
  source?: string;
}

export interface DailyNutrition {
  _id: string;
  date: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g?: number;
}

export interface DailyRecovery {
  _id: string;
  date: string;
  sleep?: { total_hours?: number; deep_hours?: number; rem_hours?: number };
  hrv_ms?: number;
  resting_heart_rate?: number;
  steps?: number;
}

export interface BodyMetric {
  _id: string;
  date: string;
  weight_lbs?: number;
  body_fat_pct?: number;
}

export interface MobileConfig {
  app: string;
  api_version: string;
  preview_mode: boolean;
  program_start: string;
  screens: Record<
    string,
    { path: string; preview_path?: string; params?: string[] }
  >;
}
