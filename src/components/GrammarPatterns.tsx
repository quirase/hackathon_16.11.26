import type { GrammarPattern } from '../types/analysis';
import { CEFR_META } from '../utils/cefr';

interface GrammarPatternsProps {
  patterns: GrammarPattern[];
}

export function GrammarPatterns({ patterns }: GrammarPatternsProps) {
  if (!patterns.length) return null;

  return (
    <section className="plate" aria-label="Detected grammar and phrasal patterns">
      <div className="plate-header">
        <h2 className="plate-title">Grammar &amp; Phrasal Patterns</h2>
        <span className="plate-meta tabular-nums">{patterns.length} structures detected</span>
      </div>

      <div className="grammar-grid">
        {patterns.map((item) => {
          const meta = CEFR_META[item.cefr];
          return (
            <div key={item.id} className="grammar-cell">
              <div className="grammar-cell-head">
                <span className="grammar-name">{item.pattern}</span>
                <div className="grammar-badges">
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
                  <span className="grammar-count tabular-nums">{item.occurrences}×</span>
                </div>
              </div>

              <p className="grammar-explanation">{item.explanation}</p>
              <blockquote className="grammar-example">&ldquo;{item.example}&rdquo;</blockquote>
            </div>
          );
        })}
      </div>
    </section>
  );
}
