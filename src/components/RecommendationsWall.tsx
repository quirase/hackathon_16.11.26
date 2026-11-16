import { ArrowLeft, ExternalLink, Play } from 'lucide-react';
import { useEffect, useState } from 'react';
import { fetchRecommendations, type RecommendedVideo } from '../api/analyzer';
import type { CefrLevel } from '../types/analysis';
import { CEFR_META, CEFR_ORDER } from '../utils/cefr';

interface RecommendationsWallProps {
  level: CefrLevel | 'ALL';
  onChangeLevel: (level: CefrLevel | 'ALL') => void;
  onSelectVideo: (url: string) => void;
  onBack: () => void;
}

export function RecommendationsWall({
  level,
  onChangeLevel,
  onSelectVideo,
  onBack,
}: RecommendationsWallProps) {
  const [items, setItems] = useState<RecommendedVideo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);
    void fetchRecommendations(level, 100).then((data) => {
      if (!active) return;
      setItems(data);
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [level]);

  return (
    <section className="plate" aria-label="Video recommendation wall">
      <div className="plate-header" style={{ flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button type="button" className="preset-chip" onClick={onBack}>
            <ArrowLeft size={14} strokeWidth={2} />
            <span>Back</span>
          </button>
          <div>
            <h1 className="plate-title" style={{ fontSize: '1.25rem' }}>
              Video Recommendation Wall
            </h1>
            <span className="plate-meta">
              {loading ? 'Loading library…' : `${items.length} video(s) saved in library`}
            </span>
          </div>
        </div>

        <div className="transcript-filter-group" role="group" aria-label="Filter wall by CEFR level">
          <button
            type="button"
            className={`filter-btn ${level === 'ALL' ? 'filter-btn--active' : ''}`}
            onClick={() => onChangeLevel('ALL')}
          >
            All
          </button>
          {CEFR_ORDER.map((lvl) => (
            <button
              key={lvl}
              type="button"
              className={`filter-btn ${level === lvl ? 'filter-btn--active' : ''}`}
              onClick={() => onChangeLevel(lvl)}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {!loading && items.length === 0 ? (
        <p className="plate-meta" style={{ padding: '32px 0', textAlign: 'center' }}>
          No {level === 'ALL' ? '' : `${level} `}videos saved yet. Analyze any YouTube video to add it here.
        </p>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
            gap: 18,
            marginTop: 16,
          }}
        >
          {items.map((item) => {
            const meta = CEFR_META[item.level] ?? CEFR_META.B1;
            const thumb =
              item.thumbnailUrl || `https://i.ytimg.com/vi/${item.videoId}/hqdefault.jpg`;
            return (
              <article
                key={item.videoId}
                style={{
                  background: 'var(--bg-canvas)',
                  border: '1px solid var(--rule-hairline)',
                  borderRadius: 'var(--radius-md)',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <button
                  type="button"
                  onClick={() => onSelectVideo(item.url)}
                  style={{
                    position: 'relative',
                    aspectRatio: '16 / 9',
                    width: '100%',
                    padding: 0,
                    border: 'none',
                    background: '#171614',
                    cursor: 'pointer',
                    overflow: 'hidden',
                  }}
                  title={`Open analysis for ${item.title}`}
                >
                  <img
                    src={thumb}
                    alt={item.title}
                    loading="lazy"
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                  />
                  <span
                    className="cefr-pill"
                    style={{
                      position: 'absolute',
                      top: 8,
                      left: 8,
                      color: meta.fg,
                      backgroundColor: meta.bg,
                      borderColor: meta.border,
                    }}
                  >
                    {item.level}
                  </span>
                  {item.durationLabel && (
                    <span
                      className="tabular-nums"
                      style={{
                        position: 'absolute',
                        bottom: 8,
                        right: 8,
                        padding: '2px 6px',
                        borderRadius: 4,
                        background: 'rgba(23, 22, 20, 0.85)',
                        color: '#FDFBF7',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                      }}
                    >
                      {item.durationLabel}
                    </span>
                  )}
                </button>

                <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6, flex: 1 }}>
                  <button
                    type="button"
                    onClick={() => onSelectVideo(item.url)}
                    style={{
                      textAlign: 'left',
                      background: 'none',
                      border: 'none',
                      padding: 0,
                      font: 'inherit',
                      fontWeight: 600,
                      fontSize: '0.92rem',
                      color: 'var(--ink-primary)',
                      cursor: 'pointer',
                      lineHeight: 1.35,
                    }}
                  >
                    {item.title}
                  </button>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto' }}>
                    <span className="plate-meta" style={{ fontSize: '0.78rem' }}>
                      {item.channel || 'YouTube'}
                    </span>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <button
                        type="button"
                        onClick={() => onSelectVideo(item.url)}
                        className="preset-chip"
                        style={{ padding: '3px 8px', fontSize: '0.75rem' }}
                      >
                        <Play size={10} strokeWidth={2.4} fill="currentColor" />
                        <span>Inspect</span>
                      </button>
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        aria-label={`Watch ${item.title} on YouTube`}
                        title="Open on YouTube"
                        style={{ color: 'var(--ink-muted)', display: 'inline-flex' }}
                      >
                        <ExternalLink size={13} strokeWidth={2} />
                      </a>
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
