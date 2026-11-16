import { Bookmark, Play } from 'lucide-react';
import { useState } from 'react';
import type { CefrLevel, TranscriptToken } from '../types/analysis';
import { CEFR_META, isCefrAtLeast } from '../utils/cefr';

interface TranscriptExcerptProps {
  tokens: TranscriptToken[];
  onSeekTo: (seconds: number) => void;
  isWordSaved: (word: string) => boolean;
  onToggleSaveToken: (token: TranscriptToken) => void;
}

type HighlightFilter = 'ALL' | 'B2' | 'C1';

export function TranscriptExcerpt({
  tokens,
  onSeekTo,
  isWordSaved,
  onToggleSaveToken,
}: TranscriptExcerptProps) {
  const [filter, setFilter] = useState<HighlightFilter>('ALL');
  const firstAnnotated = tokens.findIndex((t) => Boolean(t.cefr));
  const [selectedIndex, setSelectedIndex] = useState<number | null>(
    firstAnnotated >= 0 ? firstAnnotated : null
  );

  const selectedToken = selectedIndex !== null ? tokens[selectedIndex] : null;
  const selectedMeta = selectedToken?.cefr ? CEFR_META[selectedToken.cefr] : null;
  const selectedSaved = selectedToken ? isWordSaved(selectedToken.text) : false;

  const shouldHighlight = (cefr?: CefrLevel): boolean => {
    if (!cefr) return false;
    if (filter === 'ALL') return true;
    return isCefrAtLeast(cefr, filter);
  };

  return (
    <section className="plate" aria-label="Interactive CEFR transcript excerpt">
      <div className="plate-header">
        <h2 className="plate-title">Annotated Transcript Excerpt</h2>

        <div className="transcript-filter-group" role="group" aria-label="Filter highlighted CEFR levels">
          {(['ALL', 'B2', 'C1'] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              className={`filter-btn ${filter === mode ? 'filter-btn--active' : ''}`}
              onClick={() => setFilter(mode)}
            >
              {mode === 'ALL' ? 'All Levels' : `${mode}+ Only`}
            </button>
          ))}
        </div>
      </div>

      <div className="transcript-layout">
        <div className="transcript-body">
          {tokens.map((token, idx) => {
            const active = shouldHighlight(token.cefr);
            if (!active || !token.cefr) {
              return <span key={idx}>{token.text}</span>;
            }

            const meta = CEFR_META[token.cefr];
            const isSelected = idx === selectedIndex;

            return (
              <button
                key={idx}
                type="button"
                className={`token-highlight ${isSelected ? 'token-highlight--selected' : ''}`}
                style={{
                  borderBottomColor: meta.fg,
                  backgroundColor: isSelected ? meta.bg : 'transparent',
                }}
                onClick={() => setSelectedIndex(idx)}
              >
                {token.text}
              </button>
            );
          })}
        </div>

        <aside className="marginalia" aria-live="polite">
          {selectedToken && selectedMeta ? (
            <>
              <div>
                <div style={{ marginBottom: 10 }}>
                  <span
                    className="cefr-pill"
                    style={{
                      color: selectedMeta.fg,
                      backgroundColor: selectedMeta.bg,
                      borderColor: selectedMeta.border,
                    }}
                  >
                    {selectedToken.cefr} · {selectedMeta.name}
                  </span>
                </div>
                <h3 className="marginalia-word">{selectedToken.text}</h3>
                {selectedToken.pos && <div className="marginalia-pos">{selectedToken.pos}</div>}
                {selectedToken.definition && (
                  <p className="marginalia-def">{selectedToken.definition}</p>
                )}
              </div>

              <div className="marginalia-actions">
                {typeof selectedToken.timestampSec === 'number' && (
                  <button
                    type="button"
                    className="jump-clip-btn"
                    onClick={() => onSeekTo(selectedToken.timestampSec!)}
                  >
                    <Play size={13} strokeWidth={2.2} fill="currentColor" aria-hidden="true" />
                    <span className="tabular-nums">
                      Jump to {Math.floor(selectedToken.timestampSec / 60)}:
                      {String(selectedToken.timestampSec % 60).padStart(2, '0')}
                    </span>
                  </button>
                )}

                <button
                  type="button"
                  className={`jump-clip-btn ${selectedSaved ? 'jump-clip-btn--saved' : ''}`}
                  onClick={() => onToggleSaveToken(selectedToken)}
                >
                  <Bookmark
                    size={13}
                    strokeWidth={2}
                    fill={selectedSaved ? 'currentColor' : 'none'}
                    aria-hidden="true"
                  />
                  <span>{selectedSaved ? 'Saved' : 'Save Word'}</span>
                </button>
              </div>
            </>
          ) : (
            <p className="marginalia-empty">
              Select any underlined word in the transcript to inspect its CEFR tier, part of speech,
              and definition.
            </p>
          )}
        </aside>
      </div>
    </section>
  );
}
