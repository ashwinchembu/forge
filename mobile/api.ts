/**
 * Forge API client for React Native / Expo.
 *
 * Usage:
 *   import { ForgeAPI } from './api';
 *   const api = new ForgeAPI({ baseUrl: 'http://localhost:8000', preview: true });
 *   const dashboard = await api.getDashboard();
 */

import type {
  BodyMetric,
  DailyAnalysis,
  DailyNutrition,
  DailyRecovery,
  MobileConfig,
  Workout,
} from "./types";

export type ForgeAPIOptions = {
  baseUrl: string;
  preview?: boolean;
  programStart?: string;
};

export class ForgeAPI {
  private baseUrl: string;
  private preview: boolean;
  private programStart: string;

  constructor(options: ForgeAPIOptions) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.preview = options.preview ?? false;
    this.programStart = options.programStart ?? "2026-05-19";
  }

  private path(live: string, demo: string): string {
    return this.preview ? demo : live;
  }

  private async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    }
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`Forge API ${res.status}: ${await res.text()}`);
    return res.json() as Promise<T>;
  }

  async getConfig(): Promise<MobileConfig> {
    return this.get("/api/mobile/config");
  }

  async getHealth(): Promise<{ status: string; preview_mode: boolean }> {
    return this.get("/api/mobile/health");
  }

  /** Dashboard screen */
  async getDashboard(week?: number): Promise<DailyAnalysis> {
    if (this.preview) {
      return this.get("/api/preview/dashboard");
    }
    return this.get("/api/analysis/today", {
      program_start: this.programStart,
    });
  }

  /** Today's workout targets */
  async getWorkoutTargets(week: number) {
    return this.get(
      this.path(`/api/program/targets/${week}`, `/api/preview/program/week/${week}`)
    );
  }

  async getWorkouts(days = 7): Promise<Workout[]> {
    return this.get(
      this.path("/api/workouts", "/api/preview/workouts"),
      this.preview ? undefined : { days: String(days) }
    );
  }

  async getNutrition(days = 7): Promise<DailyNutrition[]> {
    return this.get(
      this.path("/api/nutrition", "/api/preview/nutrition"),
      this.preview ? undefined : { days: String(days) }
    );
  }

  async getRecovery(days = 7): Promise<DailyRecovery[]> {
    return this.get(
      this.path("/api/recovery", "/api/preview/recovery"),
      this.preview ? undefined : { days: String(days) }
    );
  }

  async getBodyMetrics(days = 30): Promise<BodyMetric[]> {
    return this.get(
      this.path("/api/body-metrics", "/api/preview/body-metrics"),
      this.preview ? undefined : { days: String(days) }
    );
  }

  async getSchedule(): Promise<Record<string, string>> {
    return this.get("/api/program/schedule");
  }
}
