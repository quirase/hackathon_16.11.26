export type CefrLevel = 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';

export interface SubMetric {
  id: 'speechRate' | 'vocabulary' | 'grammar' | 'clarity';
  label: string;
  value: string;
  score: number; // 0 to 100
  detail: string;
  badge?: string;
}

export interface VocabDistributionItem {
  level: CefrLevel;
  percentage: number; // 0 to 100, sum ~100
}

export interface TimelineSegment {
  id: string;
  startSec: number;
  endSec: number;
  startLabel: string;
  endLabel: string;
  level: CefrLevel;
  wpm: number;
  intensity: number; // 0 to 100
  note: string;
}

export interface GrammarPattern {
  id: string;
  pattern: string;
  cefr: CefrLevel;
  occurrences: number;
  explanation: string;
  example: string;
}

export interface FlaggedPhrase {
  id: string;
  timestampSec: number;
  timestampLabel: string;
  phrase: string;
  cefr: CefrLevel;
  partOfSpeech: string;
  meaning: string;
  contextSentence: string;
}

export interface TranscriptToken {
  text: string;
  cefr?: CefrLevel;
  pos?: string;
  definition?: string;
  timestampSec?: number;
}

export interface SavedWordItem {
  id: string;
  word: string;
  cefr: CefrLevel;
  partOfSpeech: string;
  meaning: string;
  contextSentence?: string;
  videoTitle: string;
  videoId: string;
  timestampSec?: number;
  savedAt: string;
}

export interface VideoAnalysisResult {
  id: string;
  videoId: string;
  url: string;
  title: string;
  channel: string;
  durationLabel: string;
  thumbnailUrl: string;
  detectedLevel: CefrLevel;
  confidence: number; // 0 to 100
  summary: string;
  learnerFit: string;
  analyzedAt: string;
  metrics: SubMetric[];
  vocabDistribution: VocabDistributionItem[];
  timeline: TimelineSegment[];
  grammarPatterns: GrammarPattern[];
  flaggedPhrases: FlaggedPhrase[];
  transcriptExcerpt: TranscriptToken[];
  isMock?: boolean;
}

export interface VideoAnalysisRequest {
  url: string;
}
