import type { SubMetric } from '../types/analysis';

interface MetricsGridProps {
  metrics: SubMetric[];
}

export function MetricsGrid({ metrics }: MetricsGridProps) {
  return (
    <section className="metrics-strip" aria-label="Linguistic and delivery breakdown">
      {metrics.map((metric) => (
        <div key={metric.id} className="metric-cell">
          <div className="metric-head">
            <span className="metric-label">{metric.label}</span>
            {metric.badge && <span className="metric-badge">{metric.badge}</span>}
          </div>

          <div className="metric-value tabular-nums">{metric.value}</div>

          <div className="metric-bar-track" aria-hidden="true">
            <div
              className="metric-bar-fill"
              style={{ transform: `scaleX(${Math.max(0.04, Math.min(1, metric.score / 100))})` }}
            />
          </div>

          <p className="metric-detail">{metric.detail}</p>
        </div>
      ))}
    </section>
  );
}
