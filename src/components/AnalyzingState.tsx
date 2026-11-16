import { Check } from 'lucide-react';
import { useEffect, useState } from 'react';

const STAGES = [
  'Fetching video & transcript',
  'Measuring speech rate (WPM)',
  'Profiling vocabulary bands',
  'Computing CEFR verdict',
];

export function AnalyzingState() {
  const [activeStage, setActiveStage] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveStage((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 340);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="analyzing-plate" aria-live="polite" aria-label="Analysis in progress">
      <div className="analyzing-head">
        <div className="spinner" aria-hidden="true" />
        <h2 className="analyzing-title">Analyzing English proficiency…</h2>
      </div>

      <div className="stage-list">
        {STAGES.map((label, idx) => {
          const isDone = idx < activeStage;
          const isActive = idx === activeStage;
          return (
            <div
              key={label}
              className={`stage-item ${isActive ? 'stage-item--active' : ''} ${
                isDone ? 'stage-item--done' : ''
              }`}
            >
              {isDone ? <Check size={15} strokeWidth={2.4} aria-hidden="true" /> : null}
              <span>{label}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
