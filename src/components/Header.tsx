import { Bookmark, History } from 'lucide-react';
import { isMockMode } from '../api/analyzer';

interface HeaderProps {
  historyCount: number;
  wordlistCount: number;
  onOpenHistory: () => void;
  onOpenWordlist: () => void;
  onResetHome: () => void;
}

export function Header({
  historyCount,
  wordlistCount,
  onOpenHistory,
  onOpenWordlist,
  onResetHome,
}: HeaderProps) {
  const mock = isMockMode();

  return (
    <header className="masthead">
      <div className="container masthead-inner">
        <a
          href="#top"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            onResetHome();
          }}
        >
          <span className="brand-mark">LexisTube</span>
          <span className="brand-tag">English CEFR Proficiency Analyzer</span>
        </a>

        <div className="masthead-actions">
          <div
            className="status-chip"
            title={mock ? 'Using built-in mock responses' : 'Connected to backend API'}
          >
            <span className={`status-dot ${mock ? '' : 'status-dot--live'}`} aria-hidden="true" />
            <span>{mock ? 'Mock Preview' : 'API Live'}</span>
          </div>

          <button type="button" className="history-trigger" onClick={onOpenWordlist}>
            <Bookmark size={14} strokeWidth={1.9} aria-hidden="true" />
            <span>Wordlist</span>
            <span className="history-count tabular-nums">{wordlistCount}</span>
          </button>

          <button type="button" className="history-trigger" onClick={onOpenHistory}>
            <History size={15} strokeWidth={1.9} aria-hidden="true" />
            <span>History</span>
            <span className="history-count tabular-nums">{historyCount}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
