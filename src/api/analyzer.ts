import type { CefrLevel, VideoAnalysisRequest, VideoAnalysisResult } from '../types/analysis';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';
const USE_MOCK =
  import.meta.env.VITE_USE_MOCK === 'true' ||
  (!API_BASE_URL && import.meta.env.VITE_USE_MOCK !== 'false');

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

const MOCK_LIBRARY: Record<string, Omit<VideoAnalysisResult, 'id' | 'analyzedAt' | 'url' | 'isMock'>> = {
  '8S0FDjFBj8o': {
    videoId: '8S0FDjFBj8o',
    title: 'How to Sound Smart in Your TEDx Talk',
    channel: 'TEDx Talks',
    durationLabel: '05:54',
    thumbnailUrl: 'https://i.ytimg.com/vi/8S0FDjFBj8o/hqdefault.jpg',
    detectedLevel: 'A2',
    confidence: 91,
    summary:
      'Deliberately paced, conversational English built around short declarative sentences, familiar concrete nouns, and frequent pauses for audience comprehension.',
    learnerFit: 'Ideal for A2–B1 learners practicing listening rhythm and everyday phrasing without dense idioms.',
    metrics: [
      {
        id: 'speechRate',
        label: 'Speech Rate',
        value: '118 WPM',
        score: 34,
        detail: 'Measured, unhurried delivery with clear clause boundaries.',
        badge: 'Measured',
      },
      {
        id: 'vocabulary',
        label: 'Vocabulary Difficulty',
        value: '84% Core',
        score: 32,
        detail: 'Predominantly top-1,500 high-frequency English lemmas.',
        badge: 'Elementary',
      },
      {
        id: 'grammar',
        label: 'Grammar Complexity',
        value: '1.3 Clauses',
        score: 28,
        detail: 'Simple present/past structures with minimal subordination.',
        badge: 'Direct',
      },
      {
        id: 'clarity',
        label: 'Accent & Clarity',
        value: '96 / 100',
        score: 96,
        detail: 'Studio microphone audio with crisp consonant articulation.',
        badge: 'Crisp',
      },
    ],
    vocabDistribution: [
      { level: 'A1', percentage: 52 },
      { level: 'A2', percentage: 32 },
      { level: 'B1', percentage: 11 },
      { level: 'B2', percentage: 4 },
      { level: 'C1', percentage: 1 },
      { level: 'C2', percentage: 0 },
    ],
    timeline: [
      { id: 't1', startSec: 0, endSec: 70, startLabel: '0:00', endLabel: '1:10', level: 'A2', wpm: 112, intensity: 30, note: 'Slow intro & stage framing' },
      { id: 't2', startSec: 70, endSec: 140, startLabel: '1:10', endLabel: '2:20', level: 'A2', wpm: 118, intensity: 38, note: 'Simple imperatives & gestures' },
      { id: 't3', startSec: 140, endSec: 210, startLabel: '2:20', endLabel: '3:30', level: 'B1', wpm: 126, intensity: 48, note: 'Brief comedic contrast' },
      { id: 't4', startSec: 210, endSec: 280, startLabel: '3:30', endLabel: '4:40', level: 'B1', wpm: 124, intensity: 45, note: 'Rhetorical questions' },
      { id: 't5', startSec: 280, endSec: 354, startLabel: '4:40', endLabel: '5:54', level: 'A2', wpm: 110, intensity: 28, note: 'Measured closing recap' },
    ],
    grammarPatterns: [
      {
        id: 'g1',
        pattern: 'Imperative Instructions',
        cefr: 'A1',
        occurrences: 14,
        explanation: 'Direct base-verb commands used to guide the audience step by step.',
        example: 'Walk onto the stage, look around, and pause.',
      },
      {
        id: 'g2',
        pattern: 'Going-to Future Intention',
        cefr: 'A2',
        occurrences: 6,
        explanation: 'Clear signposting of upcoming points using "be going to + verb".',
        example: 'I am going to talk about literally nothing.',
      },
      {
        id: 'g3',
        pattern: 'Zero & First Conditionals',
        cefr: 'B1',
        occurrences: 5,
        explanation: 'Cause-and-effect framing with simple present and "will/can".',
        example: 'If you speak slowly, people will assume it is important.',
      },
    ],
    flaggedPhrases: [
      {
        id: 'p1',
        timestampSec: 28,
        timestampLabel: '00:28',
        phrase: 'literally nothing',
        cefr: 'B1',
        partOfSpeech: 'adverbial phrase',
        meaning: 'Used for emphasis to mean completely nothing at all.',
        contextSentence: 'I am going to talk about literally nothing for five minutes.',
      },
      {
        id: 'p2',
        timestampSec: 74,
        timestampLabel: '01:14',
        phrase: 'meaningful gesture',
        cefr: 'B1',
        partOfSpeech: 'noun phrase',
        meaning: 'A hand or body movement intended to look important.',
        contextSentence: 'Pair every simple sentence with a slow, meaningful gesture.',
      },
      {
        id: 'p3',
        timestampSec: 132,
        timestampLabel: '02:12',
        phrase: 'dramatic pause',
        cefr: 'B1',
        partOfSpeech: 'noun phrase',
        meaning: 'A brief silence used to build attention before a key point.',
        contextSentence: 'Give the audience a dramatic pause so they expect insight.',
      },
      {
        id: 'p4',
        timestampSec: 215,
        timestampLabel: '03:35',
        phrase: 'rhetorical question',
        cefr: 'B2',
        partOfSpeech: 'noun phrase',
        meaning: 'A question asked to make a point rather than get an answer.',
        contextSentence: 'Ask a rhetorical question and nod slowly afterward.',
      },
    ],
    transcriptExcerpt: [
      { text: 'Good evening. Today I want to show you how ' },
      {
        text: 'simple',
        cefr: 'A1',
        pos: 'adjective',
        definition: 'Easy to understand or do; not complicated.',
        timestampSec: 18,
      },
      { text: ' body language and a ' },
      {
        text: 'dramatic pause',
        cefr: 'B1',
        pos: 'noun phrase',
        definition: 'A deliberate silence used to create tension or emphasis.',
        timestampSec: 132,
      },
      { text: ' can make ' },
      {
        text: 'literally nothing',
        cefr: 'B1',
        pos: 'adverbial phrase',
        definition: 'Used emphatically to mean nothing whatsoever.',
        timestampSec: 28,
      },
      { text: ' sound like a ' },
      {
        text: 'profound',
        cefr: 'B2',
        pos: 'adjective',
        definition: 'Having deep meaning or great intellectual insight.',
        timestampSec: 145,
      },
      { text: ' idea. When you walk onto a stage, speak slowly, use a ' },
      {
        text: 'meaningful gesture',
        cefr: 'B1',
        pos: 'noun phrase',
        definition: 'An intentional physical movement meant to signal importance.',
        timestampSec: 74,
      },
      { text: ', and follow it with a ' },
      {
        text: 'rhetorical question',
        cefr: 'B2',
        pos: 'noun phrase',
        definition: 'A question asked for effect with no expectation of an answer.',
        timestampSec: 215,
      },
      { text: ' that sounds important.' },
    ],
  },
  arj7oStGLkU: {
    videoId: 'arj7oStGLkU',
    title: 'Inside the Mind of a Master Procrastinator',
    channel: 'TED',
    durationLabel: '14:04',
    thumbnailUrl: 'https://i.ytimg.com/vi/arj7oStGLkU/hqdefault.jpg',
    detectedLevel: 'B2',
    confidence: 89,
    summary:
      'Natural native-speed storytelling combining conversational humor, metaphorical framing, and mid-tier academic vocabulary.',
    learnerFit: 'Strong match for B2 learners building stamina for extended narrative monologues and idioms.',
    metrics: [
      {
        id: 'speechRate',
        label: 'Speech Rate',
        value: '162 WPM',
        score: 68,
        detail: 'Brisk conversational tempo with rapid comedic transitions.',
        badge: 'Natural-Fast',
      },
      {
        id: 'vocabulary',
        label: 'Vocabulary Difficulty',
        value: '64% Core',
        score: 66,
        detail: 'Frequent B2 phrasal verbs, metaphors, and college-level terms.',
        badge: 'Upper-Int',
      },
      {
        id: 'grammar',
        label: 'Grammar Complexity',
        value: '2.1 Clauses',
        score: 62,
        detail: 'Mixed conditionals, relative clauses, and reported self-talk.',
        badge: 'Layered',
      },
      {
        id: 'clarity',
        label: 'Accent & Clarity',
        value: '91 / 100',
        score: 91,
        detail: 'General American accent; clear diction despite brisk pacing.',
        badge: 'Clear',
      },
    ],
    vocabDistribution: [
      { level: 'A1', percentage: 38 },
      { level: 'A2', percentage: 26 },
      { level: 'B1', percentage: 18 },
      { level: 'B2', percentage: 13 },
      { level: 'C1', percentage: 4 },
      { level: 'C2', percentage: 1 },
    ],
    timeline: [
      { id: 't1', startSec: 0, endSec: 168, startLabel: '0:00', endLabel: '2:48', level: 'B2', wpm: 158, intensity: 62, note: 'College thesis anecdote' },
      { id: 't2', startSec: 168, endSec: 336, startLabel: '2:48', endLabel: '5:36', level: 'B2', wpm: 166, intensity: 72, note: 'Brain metaphor & rapid banter' },
      { id: 't3', startSec: 336, endSec: 504, startLabel: '5:36', endLabel: '8:24', level: 'C1', wpm: 171, intensity: 82, note: 'Panic Monster & abstract terms' },
      { id: 't4', startSec: 504, endSec: 672, startLabel: '8:24', endLabel: '11:12', level: 'B2', wpm: 155, intensity: 64, note: 'Two types of procrastination' },
      { id: 't5', startSec: 672, endSec: 844, startLabel: '11:12', endLabel: '14:04', level: 'B1', wpm: 146, intensity: 52, note: 'Life Calendar reflective close' },
    ],
    grammarPatterns: [
      {
        id: 'g1',
        pattern: 'Past Habitual ("used to")',
        cefr: 'B1',
        occurrences: 8,
        explanation: 'Used to contrast past college habits with present reflection.',
        example: 'I used to pull an all-nighter before every major deadline.',
      },
      {
        id: 'g2',
        pattern: 'Idiomatic Phrasal Verbs',
        cefr: 'B2',
        occurrences: 19,
        explanation: 'Conversational multi-word verbs carrying non-literal meaning.',
        example: 'The monkey takes over the wheel and puts off hard work.',
      },
      {
        id: 'g3',
        pattern: 'Non-Defining Relative Clauses',
        cefr: 'B2',
        occurrences: 11,
        explanation: 'Embedded commentary clauses that layer humor onto the main narrative.',
        example: 'The Panic Monster, which is dormant most of the time, suddenly wakes up.',
      },
    ],
    flaggedPhrases: [
      {
        id: 'b1',
        timestampSec: 46,
        timestampLabel: '00:46',
        phrase: 'all-nighter',
        cefr: 'B2',
        partOfSpeech: 'noun (informal)',
        meaning: 'Staying awake through the entire night to finish work or study.',
        contextSentence: 'I had to pull an all-nighter to finish a ninety-page thesis.',
      },
      {
        id: 'b2',
        timestampSec: 118,
        timestampLabel: '01:58',
        phrase: 'instant gratification',
        cefr: 'C1',
        partOfSpeech: 'noun phrase',
        meaning: 'The desire to experience pleasure or fulfillment without delay.',
        contextSentence: 'The monkey only cares about two things: easy and fun, or instant gratification.',
      },
      {
        id: 'b3',
        timestampSec: 204,
        timestampLabel: '03:24',
        phrase: 'rational decision-maker',
        cefr: 'B2',
        partOfSpeech: 'noun phrase',
        meaning: 'The logical part of a person that plans ahead.',
        contextSentence: 'Inside the procrastinator’s brain, the rational decision-maker sits at the wheel.',
      },
      {
        id: 'b4',
        timestampSec: 342,
        timestampLabel: '05:42',
        phrase: 'hibernate in the shadows',
        cefr: 'C1',
        partOfSpeech: 'verb phrase',
        meaning: 'To remain dormant or hidden until triggered by urgency.',
        contextSentence: 'The Panic Monster is dormant most of the time, hibernating in the shadows.',
      },
    ],
    transcriptExcerpt: [
      { text: 'In college, I used to ' },
      {
        text: 'procrastinate',
        cefr: 'B2',
        pos: 'verb',
        definition: 'To delay or postpone an action out of habit or avoidance.',
        timestampSec: 32,
      },
      { text: ' on every major paper until I had no choice but to pull an ' },
      {
        text: 'all-nighter',
        cefr: 'B2',
        pos: 'noun',
        definition: 'A night spent working or studying without sleep.',
        timestampSec: 46,
      },
      { text: '. When we imaged the brain, we found a ' },
      {
        text: 'rational decision-maker',
        cefr: 'B2',
        pos: 'noun phrase',
        definition: 'The logical agent responsible for long-term planning.',
        timestampSec: 204,
      },
      { text: ' constantly battling a monkey obsessed with ' },
      {
        text: 'instant gratification',
        cefr: 'C1',
        pos: 'noun phrase',
        definition: 'Immediate reward without waiting for future benefit.',
        timestampSec: 118,
      },
      { text: ', while the Panic Monster ' },
      {
        text: 'hibernates',
        cefr: 'C1',
        pos: 'verb',
        definition: 'Remains inactive or dormant for an extended period.',
        timestampSec: 342,
      },
      { text: ' until a deadline approaches.' },
    ],
  },
  eIho2S0ZahI: {
    videoId: 'eIho2S0ZahI',
    title: 'How to Speak So That People Want to Listen',
    channel: 'TED',
    durationLabel: '09:58',
    thumbnailUrl: 'https://i.ytimg.com/vi/eIho2S0ZahI/hqdefault.jpg',
    detectedLevel: 'C1',
    confidence: 93,
    summary:
      'Polished British rhetorical prose featuring abstract nouns, low-frequency evaluative adjectives, and tightly compressed metaphors.',
    learnerFit: 'Best suited for C1–C2 learners refining register, vocal nuance, and academic/professional vocabulary.',
    metrics: [
      {
        id: 'speechRate',
        label: 'Speech Rate',
        value: '148 WPM',
        score: 58,
        detail: 'Controlled cadence with deliberate prosodic emphasis.',
        badge: 'Measured-Crisp',
      },
      {
        id: 'vocabulary',
        label: 'Vocabulary Difficulty',
        value: '46% Core',
        score: 84,
        detail: 'High density of C1–C2 abstract lexis and rhetorical terms.',
        badge: 'Advanced',
      },
      {
        id: 'grammar',
        label: 'Grammar Complexity',
        value: '2.6 Clauses',
        score: 79,
        detail: 'Parallelism, nominalizations, and embedded participial phrases.',
        badge: 'Complex',
      },
      {
        id: 'clarity',
        label: 'Accent & Clarity',
        value: '95 / 100',
        score: 95,
        detail: 'Received Pronunciation with exemplary studio articulation.',
        badge: 'Exemplary',
      },
    ],
    vocabDistribution: [
      { level: 'A1', percentage: 27 },
      { level: 'A2', percentage: 19 },
      { level: 'B1', percentage: 21 },
      { level: 'B2', percentage: 17 },
      { level: 'C1', percentage: 11 },
      { level: 'C2', percentage: 5 },
    ],
    timeline: [
      { id: 't1', startSec: 0, endSec: 120, startLabel: '0:00', endLabel: '2:00', level: 'B2', wpm: 142, intensity: 58, note: 'Seven deadly sins framework' },
      { id: 't2', startSec: 120, endSec: 240, startLabel: '2:00', endLabel: '4:00', level: 'C1', wpm: 150, intensity: 78, note: 'Abstract nouns & dogmatism' },
      { id: 't3', startSec: 240, endSec: 360, startLabel: '4:00', endLabel: '6:00', level: 'C2', wpm: 154, intensity: 88, note: 'Prosody, timbre & acoustic lexis' },
      { id: 't4', startSec: 360, endSec: 480, startLabel: '6:00', endLabel: '8:00', level: 'C1', wpm: 146, intensity: 72, note: 'Vocal warm-up demonstration' },
      { id: 't5', startSec: 480, endSec: 598, startLabel: '8:00', endLabel: '9:58', level: 'C1', wpm: 140, intensity: 68, note: 'Rhetorical synthesis' },
    ],
    grammarPatterns: [
      {
        id: 'g1',
        pattern: 'Abstract Nominalization',
        cefr: 'C1',
        occurrences: 16,
        explanation: 'Converting actions or qualities into abstract noun concepts for formal register.',
        example: 'Dogmatism is the confusion of facts with opinions.',
      },
      {
        id: 'g2',
        pattern: 'Rhetorical Parallelism',
        cefr: 'C1',
        occurrences: 9,
        explanation: 'Balanced repetition of grammatical structures for persuasive cadence.',
        example: 'Honesty, authenticity, integrity, and love.',
      },
      {
        id: 'g3',
        pattern: 'Reduced Participial Clauses',
        cefr: 'C2',
        occurrences: 7,
        explanation: 'Compact modifiers that condense cause or contrast without conjunctions.',
        example: 'Paired with expressive prosody, your words resonate across any room.',
      },
    ],
    flaggedPhrases: [
      {
        id: 'c1',
        timestampSec: 52,
        timestampLabel: '00:52',
        phrase: 'seven deadly sins',
        cefr: 'B2',
        partOfSpeech: 'idiomatic noun phrase',
        meaning: 'Metaphorical list of the worst habits in a given domain.',
        contextSentence: 'I want to suggest there are seven deadly sins of speaking.',
      },
      {
        id: 'c2',
        timestampSec: 146,
        timestampLabel: '02:26',
        phrase: 'dogmatism',
        cefr: 'C2',
        partOfSpeech: 'noun',
        meaning: 'The tendency to assert opinions as indisputable fact.',
        contextSentence: 'Sixth is dogmatism — the confusion of facts with opinions.',
      },
      {
        id: 'c3',
        timestampSec: 238,
        timestampLabel: '03:58',
        phrase: 'prosody',
        cefr: 'C2',
        partOfSpeech: 'noun',
        meaning: 'The patterns of rhythm, stress, and intonation in speech.',
        contextSentence: 'Prosody is the sing-song, the meta-language we use to impart meaning.',
      },
      {
        id: 'c4',
        timestampSec: 312,
        timestampLabel: '05:12',
        phrase: 'hailstones of speech',
        cefr: 'C1',
        partOfSpeech: 'metaphor',
        meaning: 'Rapid, unyielding remarks that overwhelm the listener.',
        contextSentence: 'Avoid the hailstones of speech when clarity and warmth matter.',
      },
    ],
    transcriptExcerpt: [
      { text: 'The human voice is the instrument we all play. Yet ' },
      {
        text: 'dogmatism',
        cefr: 'C2',
        pos: 'noun',
        definition: 'Asserting personal opinions as absolute, unquestionable truth.',
        timestampSec: 146,
      },
      { text: ' and careless ' },
      {
        text: 'exaggeration',
        cefr: 'B2',
        pos: 'noun',
        definition: 'Representing something as larger or more extreme than it is.',
        timestampSec: 120,
      },
      { text: ' erode trust. By contrast, ' },
      {
        text: 'authenticity',
        cefr: 'C1',
        pos: 'noun',
        definition: 'The quality of being genuine, honest, and true to oneself.',
        timestampSec: 194,
      },
      { text: ' paired with expressive ' },
      {
        text: 'prosody',
        cefr: 'C2',
        pos: 'noun',
        definition: 'Rhythm, stress, and intonation patterns in spoken language.',
        timestampSec: 238,
      },
      { text: ' allows your words to ' },
      {
        text: 'resonate',
        cefr: 'C1',
        pos: 'verb',
        definition: 'To evoke a deep, lasting emotional or intellectual response.',
        timestampSec: 274,
      },
      { text: ' across any room.' },
    ],
  },
};

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

  if (!USE_MOCK && API_BASE_URL) {
    const payload: VideoAnalysisRequest = { url: cleanUrl };
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      throw new Error(errorText || `Analysis failed with status ${response.status}`);
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
