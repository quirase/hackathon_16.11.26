import { AlertCircle, ArrowRight, Link2, X } from 'lucide-react';
import type { FormEvent } from 'react';
import { SAMPLE_PRESETS, type SamplePreset } from '../api/analyzer';
import { CEFR_META } from '../utils/cefr';

interface UrlInputBarProps {
  url: string;
  onUrlChange: (value: string) => void;
  onSubmit: () => void;
  onSelectPreset: (preset: SamplePreset) => void;
  isLoading: boolean;
  error: string | null;
  hasResult: boolean;
}

export function UrlInputBar({
  url,
  onUrlChange,
  onSubmit,
  onSelectPreset,
  isLoading,
  error,
  hasResult,
}: UrlInputBarProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <section className={`input-stage ${hasResult ? '' : 'input-stage--empty'}`} aria-label="Analyze YouTube video">
      {!hasResult && (
        <>
          <h1 className="page-title">Measure the English level of any YouTube video.</h1>
          <p className="page-subtitle">
            Paste a YouTube link to inspect its CEFR proficiency rating (A1–C2), speaking pace,
            lexical difficulty, and timestamped vocabulary.
          </p>
        </>
      )}

      <form className="url-form" onSubmit={handleSubmit} noValidate>
        <div className="url-input-wrap">
          <Link2 size={18} strokeWidth={1.8} className="url-input-icon" aria-hidden="true" />
          <input
            type="url"
            className="url-input"
            value={url}
            onChange={(e) => onUrlChange(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            aria-label="YouTube video URL"
            disabled={isLoading}
            autoComplete="off"
            spellCheck={false}
          />
          {url && !isLoading && (
            <button
              type="button"
              className="url-clear-btn"
              onClick={() => onUrlChange('')}
              aria-label="Clear URL"
            >
              <X size={15} strokeWidth={2} />
            </button>
          )}
        </div>

        <button type="submit" className="analyze-btn" disabled={isLoading}>
          <span>{isLoading ? 'Analyzing…' : 'Analyze Level'}</span>
          {!isLoading && <ArrowRight size={16} strokeWidth={2} aria-hidden="true" />}
        </button>
      </form>

      {error && (
        <p className="form-error" role="alert">
          <AlertCircle size={15} strokeWidth={2} aria-hidden="true" />
          <span>{error}</span>
        </p>
      )}

      <div className="presets-row">
        <span className="presets-label">Try a sample:</span>
        {SAMPLE_PRESETS.map((preset) => {
          const meta = CEFR_META[preset.cefr];
          return (
            <button
              key={preset.videoId}
              type="button"
              className="preset-chip"
              onClick={() => onSelectPreset(preset)}
              disabled={isLoading}
            >
              <span
                className="preset-cefr"
                style={{ color: meta.fg, backgroundColor: meta.bg }}
              >
                {preset.cefr}
              </span>
              <span>{preset.label}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
