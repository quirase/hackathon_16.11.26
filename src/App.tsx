import { ExternalLink, Play } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import {
  analyzeYouTubeVideo,
  fetchRecommendations,
  type RecommendedVideo,
  type SamplePreset,
} from './api/analyzer';
import { AnalyzingState } from './components/AnalyzingState';
import { DiagnosticsPlate } from './components/DiagnosticsPlate';
import { GrammarPatterns } from './components/GrammarPatterns';
import { Header } from './components/Header';
import { HeroVerdict } from './components/HeroVerdict';
import { HistoryDrawer } from './components/HistoryDrawer';
import { MetricsGrid } from './components/MetricsGrid';
import { PlayerAndPhrases } from './components/PlayerAndPhrases';
import { RecommendationsWall } from './components/RecommendationsWall';
import { TranscriptExcerpt } from './components/TranscriptExcerpt';
import { UrlInputBar } from './components/UrlInputBar';
import type {
  CefrLevel,
  FlaggedPhrase,
  SavedWordItem,
  TranscriptToken,
  VideoAnalysisResult,
} from './types/analysis';
import { CEFR_META, CEFR_ORDER } from './utils/cefr';
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

function readWallRoute(): { isWall: boolean; level: CefrLevel | 'ALL' } {
  const params = new URLSearchParams(window.location.search);
  const isWall = params.get('view') === 'wall';
  const rawLvl = (params.get('level') || 'ALL').toUpperCase();
  const level =
    rawLvl === 'ALL' || (CEFR_ORDER as string[]).includes(rawLvl)
      ? (rawLvl as CefrLevel | 'ALL')
      : 'ALL';
  return { isWall, level };
}

function getNextLevel(level: CefrLevel): CefrLevel {
  const idx = CEFR_ORDER.indexOf(level);
  return idx >= 0 && idx < CEFR_ORDER.length - 1 ? CEFR_ORDER[idx + 1] : 'C2';
}

export function App() {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VideoAnalysisResult | null>(null);
  const [history, setHistory] = useState<VideoAnalysisResult[]>(() => loadHistory());
  const [wordlist, setWordlist] = useState<SavedWordItem[]>(() => loadWordlist());
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerTab, setDrawerTab] = useState<'history' | 'wordlist'>('history');
  const [deepDiveTab, setDeepDiveTab] = useState<'transcript' | 'grammar'>('transcript');
  const [wallRoute, setWallRoute] = useState<{ isWall: boolean; level: CefrLevel | 'ALL' }>(() =>
    readWallRoute()
  );
  const [stepUpVideos, setStepUpVideos] = useState<RecommendedVideo[]>([]);

  const [activeTimestampSec, setActiveTimestampSec] = useState<number | null>(null);
  const [activePhraseId, setActivePhraseId] = useState<string | null>(null);

  useEffect(() => {
    const onPopState = () => setWallRoute(readWallRoute());
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const navigateToWall = useCallback((level: CefrLevel | 'ALL') => {
    const nextUrl = `?view=wall&level=${level}`;
    window.history.pushState({}, '', nextUrl);
    setWallRoute({ isWall: true, level });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  const navigateHome = useCallback(() => {
    if (window.location.search) {
      window.history.pushState({}, '', window.location.pathname);
    }
    setWallRoute({ isWall: false, level: 'ALL' });
  }, []);

  const runAnalysis = useCallback(
    async (targetUrl: string) => {
      navigateHome();
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
    },
    [navigateHome]
  );

  useEffect(() => {
    if (!result) {
      setStepUpVideos([]);
      return;
    }
    const nextLvl = getNextLevel(result.detectedLevel);
    let active = true;
    void fetchRecommendations(nextLvl, 6).then((items) => {
      if (!active) return;
      setStepUpVideos(items.filter((i) => i.videoId !== result.videoId).slice(0, 3));
    });
    return () => {
      active = false;
    };
  }, [result]);

  const handleSubmit = () => {
    void runAnalysis(url);
  };

  const handleSelectPreset = (preset: SamplePreset) => {
    setUrl(preset.url);
    void runAnalysis(preset.url);
  };

  const handleSelectWallVideo = (videoUrl: string) => {
    setUrl(videoUrl);
    void runAnalysis(videoUrl);
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
    navigateHome();
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

  const nextLevel = result ? getNextLevel(result.detectedLevel) : 'B2';
  const nextMeta = CEFR_META[nextLevel];

  return (
    <div id="top" className="app-shell">
      <Header
        historyCount={history.length}
        wordlistCount={wordlist.length}
        onOpenWall={() => navigateToWall('ALL')}
        onOpenHistory={() => {
          setDrawerTab('history');
          setDrawerOpen(true);
        }}
        onOpenWordlist={() => {
          setDrawerTab('wordlist');
          setDrawerOpen(true);
        }}
        onResetHome={() => {
          navigateHome();
          setResult(null);
          setError(null);
          setUrl('');
        }}
      />

      <main className="workspace">
        <div className="container">
          {wallRoute.isWall ? (
            <RecommendationsWall
              level={wallRoute.level}
              onChangeLevel={navigateToWall}
              onSelectVideo={handleSelectWallVideo}
              onBack={navigateHome}
            />
          ) : (
            <>
              <UrlInputBar
                url={url}
                onUrlChange={(val) => {
                  setUrl(val);
                  if (error) setError(null);
                }}
                onSubmit={handleSubmit}
                onSelectPreset={handleSelectPreset}
                onOpenWall={navigateToWall}
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
                    plots={result.plots}
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

                  <div
                    className="transcript-filter-group"
                    role="tablist"
                    aria-label="Deep dive view"
                    style={{ alignSelf: 'flex-start' }}
                  >
                    <button
                      type="button"
                      role="tab"
                      aria-selected={deepDiveTab === 'transcript'}
                      className={`filter-btn ${deepDiveTab === 'transcript' ? 'filter-btn--active' : ''}`}
                      onClick={() => setDeepDiveTab('transcript')}
                    >
                      Annotated Transcript
                    </button>
                    <button
                      type="button"
                      role="tab"
                      aria-selected={deepDiveTab === 'grammar'}
                      className={`filter-btn ${deepDiveTab === 'grammar' ? 'filter-btn--active' : ''}`}
                      onClick={() => setDeepDiveTab('grammar')}
                    >
                      Grammar Patterns ({result.grammarPatterns.length})
                    </button>
                  </div>

                  {deepDiveTab === 'transcript' ? (
                    <TranscriptExcerpt
                      tokens={result.transcriptExcerpt}
                      onSeekTo={(sec) => handleSeekTo(sec)}
                      isWordSaved={isWordSaved}
                      onToggleSaveToken={handleToggleSaveToken}
                    />
                  ) : (
                    <GrammarPatterns patterns={result.grammarPatterns} />
                  )}

                  {stepUpVideos.length > 0 && (
                    <section className="plate" aria-label="Next level recommendations">
                      <div className="plate-header">
                        <h2 className="plate-title">
                          Step Up to {nextLevel}
                        </h2>
                        <button
                          type="button"
                          className="preset-chip"
                          onClick={() => navigateToWall(nextLevel)}
                        >
                          <span>See all {nextLevel} videos</span>
                        </button>
                      </div>

                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                          gap: 14,
                        }}
                      >
                        {stepUpVideos.map((item) => (
                          <div
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
                              onClick={() => handleSelectWallVideo(item.url)}
                              style={{
                                position: 'relative',
                                aspectRatio: '16 / 9',
                                width: '100%',
                                padding: 0,
                                border: 'none',
                                cursor: 'pointer',
                                background: '#171614',
                              }}
                            >
                              <img
                                src={item.thumbnailUrl || `https://i.ytimg.com/vi/${item.videoId}/hqdefault.jpg`}
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
                                  color: nextMeta.fg,
                                  backgroundColor: nextMeta.bg,
                                  borderColor: nextMeta.border,
                                }}
                              >
                                {item.level}
                              </span>
                            </button>
                            <div style={{ padding: '10px 12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                              <button
                                type="button"
                                onClick={() => handleSelectWallVideo(item.url)}
                                style={{
                                  textAlign: 'left',
                                  background: 'none',
                                  border: 'none',
                                  padding: 0,
                                  font: 'inherit',
                                  fontWeight: 600,
                                  fontSize: '0.86rem',
                                  color: 'var(--ink-primary)',
                                  cursor: 'pointer',
                                }}
                              >
                                {item.title}
                              </button>
                              <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                                <button
                                  type="button"
                                  className="preset-chip"
                                  onClick={() => handleSelectWallVideo(item.url)}
                                  style={{ padding: '3px 7px', fontSize: '0.72rem' }}
                                >
                                  <Play size={10} strokeWidth={2.4} fill="currentColor" />
                                </button>
                                <a
                                  href={item.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  aria-label={`Open ${item.title} on YouTube`}
                                  style={{ color: 'var(--ink-muted)', display: 'inline-flex', alignItems: 'center' }}
                                >
                                  <ExternalLink size={13} strokeWidth={2} />
                                </a>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>
                  )}
                </div>
              )}
            </>
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
