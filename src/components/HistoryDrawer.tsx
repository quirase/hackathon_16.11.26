import { Download, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { SavedWordItem, VideoAnalysisResult } from '../types/analysis';
import { CEFR_META } from '../utils/cefr';
import { downloadAnkiCsvFromWordlist } from '../utils/export';

interface HistoryDrawerProps {
  isOpen: boolean;
  initialTab?: 'history' | 'wordlist';
  items: VideoAnalysisResult[];
  wordlist: SavedWordItem[];
  onClose: () => void;
  onSelectHistory: (item: VideoAnalysisResult) => void;
  onDeleteHistory: (videoId: string) => void;
  onClearHistory: () => void;
  onDeleteWord: (id: string) => void;
  onClearWordlist: () => void;
}

export function HistoryDrawer({
  isOpen,
  initialTab = 'history',
  items,
  wordlist,
  onClose,
  onSelectHistory,
  onDeleteHistory,
  onClearHistory,
  onDeleteWord,
  onClearWordlist,
}: HistoryDrawerProps) {
  const [tab, setTab] = useState<'history' | 'wordlist'>(initialTab);

  useEffect(() => {
    if (isOpen) setTab(initialTab);
  }, [isOpen, initialTab]);

  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="drawer-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="Library and saved wordlist"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="drawer-panel">
        <div className="drawer-header">
          <div className="drawer-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'history'}
              className={`drawer-tab ${tab === 'history' ? 'drawer-tab--active' : ''}`}
              onClick={() => setTab('history')}
            >
              <span>History</span>
              <span className="drawer-tab-count tabular-nums">{items.length}</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={tab === 'wordlist'}
              className={`drawer-tab ${tab === 'wordlist' ? 'drawer-tab--active' : ''}`}
              onClick={() => setTab('wordlist')}
            >
              <span>My Wordlist</span>
              <span className="drawer-tab-count tabular-nums">{wordlist.length}</span>
            </button>
          </div>

          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close drawer">
            <X size={16} strokeWidth={2} />
          </button>
        </div>

        {tab === 'history' ? (
          <>
            {items.length > 0 && (
              <div className="drawer-subbar">
                <span className="plate-meta">Saved in browser</span>
                <button type="button" className="text-danger-btn" onClick={onClearHistory}>
                  Clear history
                </button>
              </div>
            )}
            <div className="drawer-body">
              {items.length === 0 ? (
                <div className="history-empty">
                  No videos analyzed yet. Paste a YouTube URL or try one of the sample presets to
                  save results here for comparison.
                </div>
              ) : (
                items.map((item) => {
                  const meta = CEFR_META[item.detectedLevel];
                  const wpm = item.metrics.find((m) => m.id === 'speechRate')?.value ?? '';
                  return (
                    <div key={item.videoId} className="history-item">
                      <button
                        type="button"
                        className="history-select-btn"
                        onClick={() => {
                          onSelectHistory(item);
                          onClose();
                        }}
                      >
                        <div className="history-item-top">
                          <span
                            className="cefr-pill"
                            style={{
                              color: meta.fg,
                              backgroundColor: meta.bg,
                              borderColor: meta.border,
                            }}
                          >
                            {item.detectedLevel}
                          </span>
                          <span className="history-item-title">{item.title}</span>
                        </div>
                        <div className="history-item-meta tabular-nums">
                          <span>{item.channel}</span>
                          {wpm && <span>· {wpm}</span>}
                          <span>· {item.confidence}% conf</span>
                        </div>
                      </button>

                      <button
                        type="button"
                        className="history-delete-btn"
                        onClick={() => onDeleteHistory(item.videoId)}
                        aria-label={`Remove ${item.title} from history`}
                      >
                        <Trash2 size={15} strokeWidth={1.8} />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </>
        ) : (
          <>
            {wordlist.length > 0 && (
              <div className="drawer-subbar">
                <button
                  type="button"
                  className="study-action-btn"
                  onClick={() => downloadAnkiCsvFromWordlist(wordlist)}
                >
                  <Download size={13} strokeWidth={2} aria-hidden="true" />
                  <span>Export Wordlist CSV</span>
                </button>
                <button type="button" className="text-danger-btn" onClick={onClearWordlist}>
                  Clear all
                </button>
              </div>
            )}
            <div className="drawer-body">
              {wordlist.length === 0 ? (
                <div className="history-empty">
                  Your personal wordlist is empty. Bookmark any flagged phrase or transcript word to
                  collect it here and export to Anki.
                </div>
              ) : (
                wordlist.map((word) => {
                  const meta = CEFR_META[word.cefr];
                  return (
                    <div key={word.id} className="history-item">
                      <div className="wordlist-entry">
                        <div className="history-item-top">
                          <span
                            className="cefr-pill"
                            style={{
                              color: meta.fg,
                              backgroundColor: meta.bg,
                              borderColor: meta.border,
                            }}
                          >
                            {word.cefr}
                          </span>
                          <span className="wordlist-term">{word.word}</span>
                          {word.partOfSpeech && (
                            <span className="phrase-pos">{word.partOfSpeech}</span>
                          )}
                        </div>
                        <p className="wordlist-meaning">{word.meaning}</p>
                        <div className="history-item-meta">{word.videoTitle}</div>
                      </div>

                      <button
                        type="button"
                        className="history-delete-btn"
                        onClick={() => onDeleteWord(word.id)}
                        aria-label={`Remove ${word.word} from wordlist`}
                      >
                        <Trash2 size={15} strokeWidth={1.8} />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
