import type { FlaggedPhrase, SavedWordItem, VideoAnalysisResult } from '../types/analysis';

function escapeCsvCell(value: string): string {
  const safe = value.replace(/"/g, '""');
  return `"${safe}"`;
}

export function downloadAnkiCsvFromPhrases(phrases: FlaggedPhrase[], videoTitle: string): void {
  const header = ['Front (Phrase)', 'Back (Meaning)', 'CEFR', 'Part of Speech', 'Example', 'Source'];
  const rows = phrases.map((p) => [
    p.phrase,
    p.meaning,
    p.cefr,
    p.partOfSpeech,
    p.contextSentence,
    `${videoTitle} (${p.timestampLabel})`,
  ]);

  triggerCsvDownload([header, ...rows], `lexistube-anki-${slugify(videoTitle)}.csv`);
}

export function downloadAnkiCsvFromWordlist(words: SavedWordItem[]): void {
  const header = ['Front (Word)', 'Back (Meaning)', 'CEFR', 'Part of Speech', 'Example', 'Source'];
  const rows = words.map((w) => [
    w.word,
    w.meaning,
    w.cefr,
    w.partOfSpeech,
    w.contextSentence ?? '',
    w.videoTitle,
  ]);

  triggerCsvDownload([header, ...rows], 'lexistube-my-wordlist.csv');
}

function triggerCsvDownload(matrix: string[][], filename: string): void {
  const csvContent = matrix.map((row) => row.map(escapeCsvCell).join(',')).join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function slugify(text: string): string {
  return (
    text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 40) || 'vocabulary'
  );
}

export function buildMarkdownStudySheet(result: VideoAnalysisResult): string {
  const lines: string[] = [
    `# ${result.title}`,
    `**Channel:** ${result.channel} · **Duration:** ${result.durationLabel}`,
    `**URL:** ${result.url}`,
    '',
    `## CEFR Verdict: ${result.detectedLevel} (${result.confidence}% confidence)`,
    result.summary,
    '',
    `> **Learner Fit:** ${result.learnerFit}`,
    '',
    '## Linguistic Metrics',
    ...result.metrics.map((m) => `- **${m.label}:** ${m.value} — ${m.detail}`),
    '',
    '## Vocabulary Distribution',
    result.vocabDistribution.map((v) => `${v.level}: ${v.percentage}%`).join(' | '),
    '',
    '## Flagged Vocabulary & Phrases',
    ...result.flaggedPhrases.map(
      (p) =>
        `- **${p.phrase}** (*${p.cefr}*, ${p.partOfSpeech}, \`${p.timestampLabel}\`): ${p.meaning}\n  - Example: "${p.contextSentence}"`
    ),
    '',
    '## Grammar & Phrasal Patterns',
    ...result.grammarPatterns.map(
      (g) => `- **${g.pattern}** (*${g.cefr}*, ${g.occurrences}x): ${g.explanation} — *"${g.example}"*`
    ),
  ];

  return lines.join('\n');
}
