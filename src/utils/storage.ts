import type { SavedWordItem, VideoAnalysisResult } from '../types/analysis';

const HISTORY_STORAGE_KEY = 'lexistube_analysis_history_v1';
const WORDLIST_STORAGE_KEY = 'lexistube_saved_wordlist_v1';
const MAX_HISTORY_ITEMS = 12;

export function loadHistory(): VideoAnalysisResult[] {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveToHistory(result: VideoAnalysisResult): VideoAnalysisResult[] {
  const existing = loadHistory().filter((item) => item.videoId !== result.videoId);
  const updated = [result, ...existing].slice(0, MAX_HISTORY_ITEMS);
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // Ignore storage quota errors cleanly
  }
  return updated;
}

export function removeFromHistory(videoId: string): VideoAnalysisResult[] {
  const updated = loadHistory().filter((item) => item.videoId !== videoId);
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // Ignore
  }
  return updated;
}

export function clearHistory(): VideoAnalysisResult[] {
  try {
    localStorage.removeItem(HISTORY_STORAGE_KEY);
  } catch {
    // Ignore
  }
  return [];
}

export function loadWordlist(): SavedWordItem[] {
  try {
    const raw = localStorage.getItem(WORDLIST_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function toggleWordInWordlist(item: SavedWordItem): SavedWordItem[] {
  const existing = loadWordlist();
  const normalized = item.word.trim().toLowerCase();
  const exists = existing.some((w) => w.word.trim().toLowerCase() === normalized);

  const updated = exists
    ? existing.filter((w) => w.word.trim().toLowerCase() !== normalized)
    : [item, ...existing];

  try {
    localStorage.setItem(WORDLIST_STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // Ignore
  }
  return updated;
}

export function removeWordFromWordlist(id: string): SavedWordItem[] {
  const updated = loadWordlist().filter((w) => w.id !== id);
  try {
    localStorage.setItem(WORDLIST_STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // Ignore
  }
  return updated;
}

export function clearWordlist(): SavedWordItem[] {
  try {
    localStorage.removeItem(WORDLIST_STORAGE_KEY);
  } catch {
    // Ignore
  }
  return [];
}
