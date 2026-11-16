import { Check, Copy, Download } from 'lucide-react';
import { useState } from 'react';
import type { VideoAnalysisResult } from '../types/analysis';
import { CEFR_META, CEFR_ORDER } from '../utils/cefr';
import { buildMarkdownStudySheet, downloadAnkiCsvFromPhrases } from '../utils/export';

interface HeroVerdictProps {
  result: VideoAnalysisResult;
}

export function HeroVerdict({ result }: HeroVerdictProps) {
  const [copied, setCopied] = useState(false);
  const meta = CEFR_META[result.detectedLevel];

  const handleCopyStudySheet = async () => {
    try {
      const md = await buildMarkdownStudySheet(result);
      await navigator.clipboard.writeText(md);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard fallback ignored if blocked
    }
  };

  return (
    <section className="verdict-plate" aria-label="Detected CEFR level verdict">
      <div className="verdict-meta-bar">
        <div className="verdict-video-info">
          <span className="verdict-video-title" title={result.title}>
            {result.title}
          </span>
          <span className="verdict-mono-tag">·</span>
          <span>{result.channel}</span>
          <span className="verdict-mono-tag tabular-nums">({result.durationLabel})</span>
        </div>

        <div className="verdict-actions">
          {result.isMock && (
            <span className="mock-notice">MOCK PREVIEW — CONNECT VITE_API_BASE_URL</span>
          )}
          <button
            type="button"
            className="study-action-btn"
            onClick={() => downloadAnkiCsvFromPhrases(result.flaggedPhrases, result.title)}
            title="Download flagged vocabulary as Anki-ready CSV"
          >
            <Download size={14} strokeWidth={2} aria-hidden="true" />
            <span>Export Anki CSV</span>
          </button>
          <button
            type="button"
            className="study-action-btn"
            onClick={handleCopyStudySheet}
            title="Copy full study sheet as Markdown"
          >
            {copied ? (
              <Check size={14} strokeWidth={2.2} aria-hidden="true" />
            ) : (
              <Copy size={14} strokeWidth={2} aria-hidden="true" />
            )}
            <span>{copied ? 'Copied Sheet' : 'Copy Study Sheet'}</span>
          </button>
        </div>
      </div>

      <div className="verdict-body">
        <div
          className="cefr-stamp"
          style={{
            color: meta.fg,
            backgroundColor: meta.bg,
            borderColor: meta.border,
          }}
        >
          <span className="cefr-stamp-code">{result.detectedLevel}</span>
          <span className="cefr-stamp-name">{meta.name}</span>
          <span className="cefr-stamp-conf tabular-nums">{result.confidence}% confidence</span>
        </div>

        <div className="verdict-copy">
          <p className="verdict-summary">{result.summary}</p>
          <p className="verdict-fit">{result.learnerFit}</p>

          <div className="cefr-scale" role="list" aria-label="CEFR scale position">
            {CEFR_ORDER.map((lvl) => {
              const stepMeta = CEFR_META[lvl];
              const isActive = lvl === result.detectedLevel;
              return (
                <div
                  key={lvl}
                  role="listitem"
                  className={`cefr-step ${isActive ? 'cefr-step--active' : ''}`}
                  style={
                    isActive
                      ? {
                          color: stepMeta.fg,
                          backgroundColor: stepMeta.bg,
                          borderColor: stepMeta.border,
                        }
                      : undefined
                  }
                >
                  <span className="cefr-step-code">{lvl}</span>
                  <span>{stepMeta.name.split('-')[0]}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
