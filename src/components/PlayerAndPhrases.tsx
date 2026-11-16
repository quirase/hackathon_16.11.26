import { Bookmark, ExternalLink, Play } from 'lucide-react';
import { useEffect, useRef } from 'react';
import type { FlaggedPhrase } from '../types/analysis';
import { CEFR_META } from '../utils/cefr';

interface PlayerAndPhrasesProps {
  videoId: string;
  videoUrl: string;
  title: string;
  phrases: FlaggedPhrase[];
  activeTimestampSec: number | null;
  onSeekTo: (seconds: number, phraseId?: string) => void;
  activePhraseId: string | null;
  isWordSaved: (word: string) => boolean;
  onToggleSavePhrase: (phrase: FlaggedPhrase) => void;
}

export function PlayerAndPhrases({
  videoId,
  videoUrl,
  title,
  phrases,
  activeTimestampSec,
  onSeekTo,
  activePhraseId,
  isWordSaved,
  onToggleSavePhrase,
}: PlayerAndPhrasesProps) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  useEffect(() => {
    if (activeTimestampSec === null || !iframeRef.current?.contentWindow) return;

    const win = iframeRef.current.contentWindow;
    win.postMessage(
      JSON.stringify({
        event: 'command',
        func: 'seekTo',
        args: [activeTimestampSec, true],
      }),
      '*'
    );
    win.postMessage(
      JSON.stringify({
        event: 'command',
        func: 'playVideo',
        args: [],
      }),
      '*'
    );
  }, [activeTimestampSec]);

  const embedSrc = `https://www.youtube.com/embed/${videoId}?enablejsapi=1&rel=0&modestbranding=1`;

  return (
    <section className="studio-split" aria-label="Video player and flagged vocabulary">
      <div className="plate">
        <div className="plate-header">
          <h2 className="plate-title">Video Specimen</h2>
          <a
            href={videoUrl}
            target="_blank"
            rel="noreferrer"
            className="plate-meta"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 5, textDecoration: 'none' }}
          >
            <span>Open on YouTube</span>
            <ExternalLink size={13} strokeWidth={2} aria-hidden="true" />
          </a>
        </div>

        <div className="player-frame-wrap">
          <iframe
            ref={iframeRef}
            className="player-iframe"
            src={embedSrc}
            title={title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>

        <div className="player-caption">
          <span>Select any flagged phrase or timeline block to jump directly to its timestamp.</span>
          {activeTimestampSec !== null && (
            <span className="plate-meta tabular-nums">
              Jumped to {Math.floor(activeTimestampSec / 60)}:
              {String(activeTimestampSec % 60).padStart(2, '0')}
            </span>
          )}
        </div>
      </div>

      <div className="plate">
        <div className="plate-header">
          <h2 className="plate-title">Flagged Vocabulary &amp; Phrases</h2>
          <span className="plate-meta tabular-nums">{phrases.length} items</span>
        </div>

        <div className="phrases-list" role="list">
          {phrases.map((item) => {
            const meta = CEFR_META[item.cefr];
            const isActive = item.id === activePhraseId;
            const saved = isWordSaved(item.phrase);

            return (
              <div
                key={item.id}
                role="listitem"
                className={`phrase-row-wrap ${isActive ? 'phrase-row--active' : ''}`}
              >
                <button
                  type="button"
                  className="phrase-row"
                  onClick={() => onSeekTo(item.timestampSec, item.id)}
                >
                  <div className="phrase-row-top">
                    <div className="phrase-term-wrap">
                      <span className="phrase-term">{item.phrase}</span>
                      <span className="phrase-pos">{item.partOfSpeech}</span>
                    </div>

                    <div className="phrase-badges">
                      <span
                        className="cefr-pill"
                        style={{
                          color: meta.fg,
                          backgroundColor: meta.bg,
                          borderColor: meta.border,
                        }}
                      >
                        {item.cefr}
                      </span>
                      <span className="timestamp-btn tabular-nums">
                        <Play size={11} strokeWidth={2.4} fill="currentColor" aria-hidden="true" />
                        {item.timestampLabel}
                      </span>
                    </div>
                  </div>

                  <p className="phrase-meaning">{item.meaning}</p>
                  <p className="phrase-context">&ldquo;{item.contextSentence}&rdquo;</p>
                </button>

                <button
                  type="button"
                  className={`bookmark-btn ${saved ? 'bookmark-btn--saved' : ''}`}
                  onClick={() => onToggleSavePhrase(item)}
                  aria-label={saved ? `Remove ${item.phrase} from My Wordlist` : `Save ${item.phrase} to My Wordlist`}
                  title={saved ? 'Saved in My Wordlist' : 'Save to My Wordlist'}
                >
                  <Bookmark
                    size={15}
                    strokeWidth={1.9}
                    fill={saved ? 'currentColor' : 'none'}
                    aria-hidden="true"
                  />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
