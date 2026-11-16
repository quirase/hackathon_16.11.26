import type { CefrLevel, VideoAnalysisRequest, VideoAnalysisResult } from '../types/analysis';
import mockData from './mockData.json';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export const isMockMode = (): boolean => USE_MOCK;

export function extractYouTubeVideoId(rawUrl: string): string | null {
  const trimmed = rawUrl.trim();
  if (!trimmed) return null;

  if (/^[a-zA-Z0-9_-]{11}$/.test(trimmed)) {
    return trimmed;
  }

  try {
    const normalized = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
    const url = new URL(normalized);
    const host = url.hostname.replace(/^www\./, '').toLowerCase();

    if (host === 'youtu.be') {
      const id = url.pathname.split('/').filter(Boolean)[0];
      return id && /^[a-zA-Z0-9_-]{11}$/.test(id) ? id : null;
    }

    if (
      host === 'youtube.com' ||
      host === 'm.youtube.com' ||
      host === 'music.youtube.com' ||
      host === 'youtube-nocookie.com'
    ) {
      const vParam = url.searchParams.get('v');
      if (vParam && /^[a-zA-Z0-9_-]{11}$/.test(vParam)) {
        return vParam;
      }
      const parts = url.pathname.split('/').filter(Boolean);
      if (parts.length >= 2 && ['embed', 'shorts', 'live', 'v'].includes(parts[0])) {
        return /^[a-zA-Z0-9_-]{11}$/.test(parts[1]) ? parts[1] : null;
      }
    }
  } catch {
    return null;
  }

  return null;
}

export interface SamplePreset {
  label: string;
  cefr: CefrLevel;
  url: string;
  videoId: string;
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

type MockTemplate = Omit<VideoAnalysisResult, 'id' | 'analyzedAt' | 'url' | 'isMock'>;
const MOCK_LIBRARY = mockData as Record<string, MockTemplate>;

function deterministicFallback(videoId: string): Omit<VideoAnalysisResult, 'id' | 'analyzedAt' | 'url' | 'isMock'> {
  const levels: CefrLevel[] = ['B1', 'B2', 'C1', 'A2'];
  const hash = videoId.split('').reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  const detectedLevel = levels[hash % levels.length];
  const wpm = 128 + (hash % 45);
  const confidence = 82 + (hash % 14);

  return {
    videoId,
    title: `YouTube Video (${videoId}) — Mock Preview`,
    channel: 'Connected Video Preview',
    durationLabel: '08:24',
    thumbnailUrl: `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`,
    detectedLevel,
    confidence,
    summary:
      'Synthetic preview generated because no backend API URL is configured yet. Wire VITE_API_BASE_URL to replace this with live transcript & audio analysis.',
    learnerFit: `Estimated ${detectedLevel} difficulty profile based on mock preview parameters.`,
    metrics: [
      {
        id: 'speechRate',
        label: 'Speech Rate',
        value: `${wpm} WPM`,
        score: Math.min(95, Math.round((wpm / 210) * 100)),
        detail: 'Simulated speaking tempo for this preview.',
        badge: wpm > 155 ? 'Brisk' : 'Moderate',
      },
      {
        id: 'vocabulary',
        label: 'Vocabulary Difficulty',
        value: '68% Core',
        score: 64,
        detail: 'Estimated lexical band distribution.',
        badge: detectedLevel,
      },
      {
        id: 'grammar',
        label: 'Grammar Complexity',
        value: '1.9 Clauses',
        score: 58,
        detail: 'Estimated syntactic subordination depth.',
        badge: 'Balanced',
      },
      {
        id: 'clarity',
        label: 'Accent & Clarity',
        value: '89 / 100',
        score: 89,
        detail: 'Estimated speech intelligibility index.',
        badge: 'Clear',
      },
    ],
    vocabDistribution: [
      { level: 'A1', percentage: 36 },
      { level: 'A2', percentage: 26 },
      { level: 'B1', percentage: 19 },
      { level: 'B2', percentage: 12 },
      { level: 'C1', percentage: 5 },
      { level: 'C2', percentage: 2 },
    ],
    timeline: [
      { id: 't1', startSec: 0, endSec: 120, startLabel: '0:00', endLabel: '2:00', level: 'B1', wpm: wpm - 10, intensity: 46, note: 'Opening context' },
      { id: 't2', startSec: 120, endSec: 240, startLabel: '2:00', endLabel: '4:00', level: detectedLevel, wpm, intensity: 64, note: 'Core explanation' },
      { id: 't3', startSec: 240, endSec: 360, startLabel: '4:00', endLabel: '6:00', level: detectedLevel, wpm: wpm + 8, intensity: 72, note: 'Dense terminology' },
      { id: 't4', startSec: 360, endSec: 504, startLabel: '6:00', endLabel: '8:24', level: 'B1', wpm: wpm - 6, intensity: 50, note: 'Summary & wrap-up' },
    ],
    grammarPatterns: [
      {
        id: 'mg1',
        pattern: 'Subordinate Contrast Clauses',
        cefr: 'B2',
        occurrences: 6,
        explanation: 'Connecting contrasting ideas with "although", "whereas", or "while".',
        example: 'While the concept sounds abstract, the daily habit is straightforward.',
      },
      {
        id: 'mg2',
        pattern: 'Modal Hedging',
        cefr: 'B2',
        occurrences: 8,
        explanation: 'Softening claims using "might", "tend to", or "could indicate".',
        example: 'This pattern tends to appear in upper-intermediate explanations.',
      },
    ],
    flaggedPhrases: [
      {
        id: 'm1',
        timestampSec: 18,
        timestampLabel: '00:18',
        phrase: 'nuanced perspective',
        cefr: 'C1',
        partOfSpeech: 'noun phrase',
        meaning: 'A viewpoint that accounts for subtle distinctions.',
        contextSentence: 'Mock timestamp — click to jump the embedded player to 00:18.',
      },
      {
        id: 'm2',
        timestampSec: 64,
        timestampLabel: '01:04',
        phrase: 'take into account',
        cefr: 'B2',
        partOfSpeech: 'idiomatic verb phrase',
        meaning: 'To consider a factor when making a judgment.',
        contextSentence: 'Mock timestamp — click to jump the embedded player to 01:04.',
      },
    ],
    transcriptExcerpt: [
      { text: 'This is a ' },
      {
        text: 'synthetic',
        cefr: 'B2',
        pos: 'adjective',
        definition: 'Generated as a demonstration placeholder before connecting your backend.',
        timestampSec: 10,
      },
      { text: ' transcript preview for video ' },
      { text: videoId },
      { text: '. Once your backend returns ' },
      {
        text: 'empirical',
        cefr: 'C1',
        pos: 'adjective',
        definition: 'Based on observed, measured data rather than theory.',
        timestampSec: 32,
      },
      { text: ' CEFR token annotations, they will render interactively right here.' },
    ],
  };
}

export async function analyzeYouTubeVideo(rawUrl: string): Promise<VideoAnalysisResult> {
  const videoId = extractYouTubeVideoId(rawUrl);
  if (!videoId) {
    throw new Error('Please enter a valid YouTube URL (e.g. youtube.com/watch?v=... or youtu.be/...).');
  }

  const cleanUrl = `https://www.youtube.com/watch?v=${videoId}`;

  if (!USE_MOCK) {
    const payload: VideoAnalysisRequest = { url: cleanUrl };
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
      videoId: data.videoId || videoId,
      url: data.url || cleanUrl,
      isMock: false,
    };
  }

  await new Promise((resolve) => setTimeout(resolve, 1350));

  const template = MOCK_LIBRARY[videoId] ?? deterministicFallback(videoId);
  return {
    ...template,
    id: `${videoId}-${Date.now()}`,
    url: cleanUrl,
    analyzedAt: new Date().toISOString(),
    isMock: true,
  };
}
