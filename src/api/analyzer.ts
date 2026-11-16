import type { CefrLevel, VideoAnalysisRequest, VideoAnalysisResult } from '../types/analysis';

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export const isMockMode = (): boolean => USE_MOCK;

export interface SamplePreset {
  label: string;
  cefr: CefrLevel;
  url: string;
  videoId: string;
}

export interface RecommendedVideo {
  videoId: string;
  url: string;
  title: string;
  level: CefrLevel;
  channel?: string;
  durationLabel?: string;
  thumbnailUrl?: string;
}

export async function fetchRecommendations(
  level: CefrLevel | 'ALL',
  limit = 50
): Promise<RecommendedVideo[]> {
  if (USE_MOCK) return [];
  try {
    const res = await fetch(
      `${API_BASE_URL}/api/recommendations?level=${encodeURIComponent(level)}&limit=${limit}`
    );
    if (!res.ok) return [];
    const data = (await res.json()) as { items?: RecommendedVideo[] };
    return data.items ?? [];
  } catch {
    return [];
  }
}

export const SAMPLE_PRESETS: SamplePreset[] = [
  {
    label: 'Clear Everyday Talk',
    cefr: 'A2',
    url: 'https://www.youtube.com/watch?v=8S0FDjFBj8o',
    videoId: '8S0FDjFBj8o',
  },
  {
    label: 'Narrative Essay',
    cefr: 'B2',
    url: 'https://www.youtube.com/watch?v=arj7oStGLkU',
    videoId: 'arj7oStGLkU',
  },
  {
    label: 'Rhetoric & Acoustics',
    cefr: 'C1',
    url: 'https://www.youtube.com/watch?v=eIho2S0ZahI',
    videoId: 'eIho2S0ZahI',
  },
];

export async function analyzeYouTubeVideo(rawUrl: string): Promise<VideoAnalysisResult> {
  const trimmed = rawUrl.trim();
  if (!trimmed) {
    throw new Error('Please enter a valid YouTube URL (e.g. youtube.com/watch?v=... or youtu.be/...).');
  }

  const payload: VideoAnalysisRequest & { mock?: boolean } = {
    url: trimmed,
    ...(USE_MOCK ? { mock: true } : {}),
  };

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    let message = errorText;
    try {
      const parsed = JSON.parse(errorText) as { error?: string };
      if (parsed.error) message = parsed.error;
    } catch {
      // keep raw text
    }
    throw new Error(message || `Analysis failed with status ${response.status}`);
  }

  const data = (await response.json()) as VideoAnalysisResult;
  return {
    ...data,
    isMock: Boolean(data.isMock),
  };
}
