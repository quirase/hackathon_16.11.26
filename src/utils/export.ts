import { API_BASE_URL } from '../api/analyzer';
import type { FlaggedPhrase, SavedWordItem, VideoAnalysisResult } from '../types/analysis';

function saveBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function postAnkiExport(body: Record<string, unknown>, fallbackName: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/export/anki`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`Export failed with status ${res.status}`);
  }
  const disposition = res.headers.get('Content-Disposition') ?? '';
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match?.[1] || fallbackName;
  saveBlobDownload(await res.blob(), filename);
}

export async function downloadAnkiCsvFromPhrases(
  phrases: FlaggedPhrase[],
  videoTitle: string
): Promise<void> {
  await postAnkiExport({ mode: 'phrases', phrases, videoTitle }, 'lexistube-anki.csv');
}

export async function downloadAnkiCsvFromWordlist(words: SavedWordItem[]): Promise<void> {
  await postAnkiExport({ mode: 'wordlist', words }, 'lexistube-my-wordlist.csv');
}

export async function buildMarkdownStudySheet(result: VideoAnalysisResult): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/api/export/markdown`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ result }),
  });
  if (!res.ok) {
    throw new Error(`Markdown export failed with status ${res.status}`);
  }
  const data = (await res.json()) as { markdown: string };
  return data.markdown;
}
