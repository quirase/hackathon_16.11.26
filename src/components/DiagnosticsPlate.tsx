import { Play } from 'lucide-react';
import type { TimelineSegment, VocabDistributionItem } from '../types/analysis';
import { CEFR_META } from '../utils/cefr';

interface DiagnosticsPlateProps {
  distribution: VocabDistributionItem[];
  timeline: TimelineSegment[];
  activeTimestampSec: number | null;
  onSeekTo: (seconds: number) => void;
}

export function DiagnosticsPlate({
  distribution,
  timeline,
  activeTimestampSec,
  onSeekTo,
}: DiagnosticsPlateProps) {
  return (
    <section className="diagnostics-grid" aria-label="Lexical distribution and difficulty timeline">
      <div className="plate">
        <div className="plate-header">
          <h2 className="plate-title">Vocabulary Distribution</h2>
          <span className="plate-meta">Lexical share by CEFR band</span>
        </div>

        <div className="dist-body">
          <div className="dist-bar" role="img" aria-label="CEFR vocabulary percentage bar">
            {distribution
              .filter((item) => item.percentage > 0)
              .map((item) => {
                const meta = CEFR_META[item.level];
                return (
                  <div
                    key={item.level}
                    className="dist-segment"
                    style={{
                      width: `${item.percentage}%`,
                      backgroundColor: meta.fg,
                    }}
                    title={`${item.level} (${meta.name}): ${item.percentage}%`}
                  />
                );
              })}
          </div>

          <div className="dist-legend">
            {distribution.map((item) => {
              const meta = CEFR_META[item.level];
              return (
                <div key={item.level} className="dist-legend-item">
                  <span
                    className="dist-swatch"
                    style={{ backgroundColor: meta.fg }}
                    aria-hidden="true"
                  />
                  <span className="dist-level">{item.level}</span>
                  <span className="dist-pct tabular-nums">{item.percentage}%</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="plate">
        <div className="plate-header">
          <h2 className="plate-title">Difficulty Over Time</h2>
          <span className="plate-meta">Click any segment to jump</span>
        </div>

        <div className="timeline-strip" role="list">
          {timeline.map((seg) => {
            const meta = CEFR_META[seg.level];
            const isActive =
              activeTimestampSec !== null &&
              activeTimestampSec >= seg.startSec &&
              activeTimestampSec < seg.endSec;

            return (
              <button
                key={seg.id}
                type="button"
                role="listitem"
                className={`timeline-seg ${isActive ? 'timeline-seg--active' : ''}`}
                onClick={() => onSeekTo(seg.startSec)}
                title={`${seg.startLabel}–${seg.endLabel}: ${seg.note}`}
              >
                <div className="timeline-seg-top">
                  <span
                    className="cefr-pill"
                    style={{
                      color: meta.fg,
                      backgroundColor: meta.bg,
                      borderColor: meta.border,
                    }}
                  >
                    {seg.level}
                  </span>
                  <span className="timeline-wpm tabular-nums">{seg.wpm} WPM</span>
                </div>

                <div className="timeline-bar-wrap" aria-hidden="true">
                  <div
                    className="timeline-bar-fill"
                    style={{
                      backgroundColor: meta.fg,
                      transform: `scaleY(${Math.max(0.18, Math.min(1, seg.intensity / 100))})`,
                    }}
                  />
                </div>

                <div className="timeline-seg-foot">
                  <span className="timeline-time tabular-nums">
                    <Play size={10} strokeWidth={2.4} fill="currentColor" aria-hidden="true" />
                    {seg.startLabel}
                  </span>
                  <span className="timeline-note">{seg.note}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
}
