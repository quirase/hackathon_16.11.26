import { useCallback, useState } from 'react';
import { analyzeYouTubeVideo, type SamplePreset } from './api/analyzer';
import { AnalyzingState } from './components/AnalyzingState';
import { DiagnosticsPlate } from './components/DiagnosticsPlate';
import { GrammarPatterns } from './components/GrammarPatterns';
import { Header } from './components/Header';
import { HeroVerdict } from './components/HeroVerdict';
import { HistoryDrawer } from './components/HistoryDrawer';
import { MetricsGrid } from './components/MetricsGrid';
import { PlayerAndPhrases } from './components/PlayerAndPhrases';
import { TranscriptExcerpt } from './components/TranscriptExcerpt';
import { UrlInputBar } from './components/UrlInputBar';
import type {
  FlaggedPhrase,
  SavedWordItem,
  TranscriptToken,
  VideoAnalysisResult,
} from './types/analysis';
import {
  clearHistory,
  clearWordlist,
  loadHistory,
  loadWordlist,
  removeFromHistory,
  removeWordFromWordlist,
  saveToHistory,
  toggleWordInWordlist,
} from './utils/storage';

export function App() {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VideoAnalysisResult | null>(null);
  const [history, setHistory] = useState<VideoAnalysisResult[]>(() => loadHistory());
  const [wordlist, setWordlist] = useState<SavedWordItem[]>(() => loadWordlist());
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState<'history' | 'wordlist'>('history');

  const [activeTimestampSec, setActiveTimestampSec] = useState<number | null>(null);
  const [activePhraseId, setActivePhraseId] = useState<string | null>(null);

  const runAnalysis = useCallback(async (targetUrl: string) => {
    setError(null);
    setIsLoading(true);
    setActiveTimestampSec(null);
    setActivePhraseId(null);

    try {
      const data = await analyzeYouTubeVideo(targetUrl);
      setResult(data);
      setHistory(saveToHistory(data));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to analyze this video.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSubmit = () => {
    void runAnalysis(url);
  };

  const handleSelectPreset = (preset: SamplePreset) => {
    setUrl(preset.url);
    void runAnalysis(preset.url);
  };

  const handleSeekTo = (seconds: number, phraseId?: string) => {
    setActiveTimestampSec(null);
    window.requestAnimationFrame(() => {
      setActiveTimestampSec(seconds);
    });
    if (phraseId) {
      setActivePhraseId(phraseId);
    }
  };

  const handleSelectHistory = (item: VideoAnalysisResult) => {
    setUrl(item.url);
    setError(null);
    setResult(item);
    setActiveTimestampSec(null);
    setActivePhraseId(null);
  };

  const isWordSaved = useCallback(
    (word: string) =>
      wordlist.some((w) => w.word.trim().toLowerCase() === word.trim().toLowerCase()),
    [wordlist]
  );

  const handleToggleSavePhrase = (phrase: FlaggedPhrase) => {
    if (!result) return;
    setWordlist(
      toggleWordInWordlist({
        id: `${result.videoId}-${phrase.id}`,
        word: phrase.phrase,
        cefr: phrase.cefr,
        partOfSpeech: phrase.partOfSpeech,
        meaning: phrase.meaning,
        contextSentence: phrase.contextSentence,
        videoTitle: result.title,
        videoId: result.videoId,
        timestampSec: phrase.timestampSec,
        savedAt: new Date().toISOString(),
      })
    );
  };

  const handleToggleSaveToken = (token: TranscriptToken) => {
    if (!result || !token.cefr) return;
    setWordlist(
      toggleWordInWordlist({
        id: `${result.videoId}-${token.text.toLowerCase()}`,
        word: token.text,
        cefr: token.cefr,
        partOfSpeech: token.pos ?? 'term',
        meaning: token.definition ?? '',
        videoTitle: result.title,
        videoId: result.videoId,
        timestampSec: token.timestampSec,
        savedAt: new Date().toISOString(),
      })
    );
  };

  return (
    <div className="app-shell" id="top">
      <Header
        historyCount={history.length}
        wordlistCount={wordlist.length}
        onOpenHistory={() => {
          setDrawerTab('history');
          setDrawerOpen(true);
        }}
        onOpenWordlist={() => {
          setDrawerTab('wordlist');
          setDrawerOpen(true);
        }}
        onResetHome={() => {
          setResult(null);
          setError(null);
          setUrl('');
        }}
      />

      <main className="workspace">
        <div className="container">
          <UrlInputBar
            url={url}
            onUrlChange={(val) => {
              setUrl(val);
              if (error) setError(null);
            }}
            onSubmit={handleSubmit}
            onSelectPreset={handleSelectPreset}
            isLoading={isLoading}
            error={error}
            hasResult={Boolean(result) || isLoading}
          />

          {isLoading && <AnalyzingState />}

          {!isLoading && result && (
            <div className="results-stack" key={result.id}>
              <HeroVerdict result={result} />
              <MetricsGrid metrics={result.metrics} />
              <DiagnosticsPlate
                distribution={result.vocabDistribution}
                timeline={result.timeline}
                activeTimestampSec={activeTimestampSec}
                onSeekTo={(sec) => handleSeekTo(sec)}
              />
              <PlayerAndPhrases
                videoId={result.videoId}
                videoUrl={result.url}
                title={result.title}
                phrases={result.flaggedPhrases}
                activeTimestampSec={activeTimestampSec}
                onSeekTo={handleSeekTo}
                activePhraseId={activePhraseId}
                isWordSaved={isWordSaved}
                onToggleSavePhrase={handleToggleSavePhrase}
              />
              <GrammarPatterns patterns={result.grammarPatterns} />
              <TranscriptExcerpt
                tokens={result.transcriptExcerpt}
                onSeekTo={(sec) => handleSeekTo(sec)}
                isWordSaved={isWordSaved}
                onToggleSaveToken={handleToggleSaveToken}
              />
            </div>
          )}
        </div>
      </main>

      <HistoryDrawer
        isOpen={drawerOpen}
        initialTab={drawerTab}
        items={history}
        wordlist={wordlist}
        onClose={() => setDrawerOpen(false)}
        onSelectHistory={handleSelectHistory}
        onDeleteHistory={(videoId) => setHistory(removeFromHistory(videoId))}
        onClearHistory={() => setHistory(clearHistory())}
        onDeleteWord={(id) => setWordlist(removeWordFromWordlist(id))}
        onClearWordlist={() => setWordlist(clearWordlist())}
      />
    </div>
  );
}

export default App;
