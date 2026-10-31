import {
  type ChangeEvent,
  type ReactNode,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  AlertCircle,
  ArrowLeft,
  ArrowUpRight,
  BookOpen,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  FileCheck2,
  FileText,
  FolderOpen,
  Info,
  Loader2,
  LockKeyhole,
  Menu,
  Scale,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  UploadCloud,
  X,
  TrendingUp,
  MessageSquare,
  BarChart3,
  CheckCircle2,
  XCircle,
  GitCompare,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Bot,
  Zap,
} from 'lucide-react';
import './index.css';

// ── types ──────────────────────────────────────────────────────────────────

type RiskLevel = 'low' | 'medium' | 'high';

interface RiskDimension {
  dimension: string;
  score: number;
  rationale: string;
}

interface RiskScores {
  dimensions: RiskDimension[];
  explanation: string;
  criticalFindings: string[];
}

interface RiskItem {
  title: string;
  severity: string;
  detail: string;
  excerpt?: string;
  category?: string;
  recommendation?: string;
  strength?: string;
  type: 'red_flag' | 'green_flag';
}

interface RedFlag {
  title: string;
  severity: string;
  detail: string;
  excerpt?: string;
  category?: string;
  recommendation?: string;
}

interface GreenFlag {
  title: string;
  detail: string;
  excerpt?: string;
  category?: string;
  strength?: string;
}

interface Obligation {
  party: string;
  action: string;
  timing: string;
  status: string;
  consequence?: string;
  section?: string;
}

interface Comparison {
  clause_type: string;
  status: string;
  finding: string;
  standard_practice: string;
  deviation_level: string;
}

interface Negotiation {
  original_issue: string;
  suggested_change: string;
  negotiation_strategy: string;
  priority: string;
  fallback_position: string;
  legal_basis?: string;
}

interface AgentLogEntry {
  agent: string;
  action: string;
  result: string;
  duration_ms: number;
}

interface AnalysisResult {
  id: string;
  filename: string;
  size: number;
  documentType: string;
  summary: string;
  riskLevel: RiskLevel;
  overallScore: number;
  riskScores: RiskScores;
  risks: RiskItem[];
  redFlags: RedFlag[];
  greenFlags: GreenFlag[];
  obligations: Obligation[];
  comparisons: Comparison[];
  negotiations: Negotiation[];
  keyTerms: string[];
  parties: string[];
  agentsCompleted: string[];
  executionLog: AgentLogEntry[];
  createdAt: string;
}

interface LibraryDoc {
  id: string;
  filename: string;
  size: number;
  documentType: string;
  riskLevel: RiskLevel;
  overallScore: number;
  createdAt: string;
}

// ── helpers ────────────────────────────────────────────────────────────────

const API_BASE = 'http://localhost:5000/api';

function formatBytes(bytes: number) {
  if (!bytes) return '—';
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Recently added';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
}

function cn(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(' ');
}

// ── shared components ──────────────────────────────────────────────────────

function RiskBadge({ level, compact = false }: { level: string; compact?: boolean }) {
  const style =
    level === 'high'
      ? 'bg-[#f8e1dc] text-[#983d35] border-[#e9b9b0]'
      : level === 'medium'
        ? 'bg-[#fff0d7] text-[#9a651d] border-[#edcf9d]'
        : 'bg-[#dceee7] text-[#286a59] border-[#b9dccc]';
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono-app text-[10px] font-bold uppercase tracking-[.11em]',
        style,
        compact && 'px-2 py-0.5 text-[9px]',
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {level} risk
    </span>
  );
}

function ScoreMeter({ score }: { score: number }) {
  const color = score <= 35 ? '#286a59' : score <= 65 ? '#9a651d' : '#983d35';
  const pct = Math.min(100, Math.max(0, score));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] font-mono-app text-muted-foreground">
        <span>Risk Score</span>
        <span style={{ color }} className="font-bold">{score}/100</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function Logo() {
  return (
    <button
      onClick={() => setView('library')}
      className="flex items-center gap-3 text-foreground no-underline bg-transparent border-0 cursor-pointer p-0"
    >
      <span className="grid h-9 w-9 place-items-center rounded-[11px] bg-primary text-primary-foreground shadow-[0_5px_16px_hsl(var(--primary)/.18)]">
        <Scale size={19} strokeWidth={1.8} />
      </span>
      <span className="font-semibold tracking-[-.03em]">ClearClause</span>
    </button>
  );
}

// global view state — simple since no router needed
type View = 'library' | 'detail';
let setView: (v: View) => void = () => {};
let setSelectedDoc: (d: AnalysisResult | null) => void = () => {};

// ── shell ──────────────────────────────────────────────────────────────────

function Shell({ children, onHome }: { children: ReactNode; onHome: () => void }) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className="grain min-h-[100dvh] bg-background">
      <header className="border-b border-border/80 bg-[#f8f6ef]/85 backdrop-blur-md">
        <div className="mx-auto flex h-[72px] max-w-[1440px] items-center justify-between px-5 sm:px-8 lg:px-12">
          <button
            onClick={onHome}
            className="flex items-center gap-3 text-foreground bg-transparent border-0 cursor-pointer p-0"
          >
            <span className="grid h-9 w-9 place-items-center rounded-[11px] bg-primary text-primary-foreground shadow-[0_5px_16px_hsl(var(--primary)/.18)]">
              <Scale size={19} strokeWidth={1.8} />
            </span>
            <span className="font-semibold tracking-[-.03em]">ClearClause</span>
          </button>
          <nav
            className={cn(
              'absolute left-0 right-0 top-[72px] z-20 border-b border-border bg-[#f8f6ef] px-5 py-4 shadow-lg md:static md:flex md:items-center md:gap-8 md:border-0 md:bg-transparent md:p-0 md:shadow-none',
              !menuOpen && 'hidden md:flex',
            )}
          >
            <button
              onClick={onHome}
              className="block py-2 text-sm font-medium text-foreground/75 transition-colors hover:text-primary bg-transparent border-0 cursor-pointer"
            >
              Library
            </button>
            <button
              className="flex items-center gap-2 py-2 text-sm font-medium text-foreground/75 transition-colors hover:text-primary bg-transparent border-0 cursor-pointer"
              onClick={() => setMenuOpen(false)}
            >
              <CircleHelp size={16} /> How it works
            </button>
          </nav>
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="hidden items-center gap-2 text-xs text-muted-foreground sm:flex">
              <LockKeyhole size={13} className="text-primary" /> RAG-Powered · Agentic AI
            </div>
            <button
              onClick={() => setMenuOpen((c) => !c)}
              className="rounded-lg p-2 text-muted-foreground hover:bg-muted md:hidden bg-transparent border-0 cursor-pointer"
            >
              {menuOpen ? <X size={19} /> : <Menu size={19} />}
            </button>
          </div>
        </div>
      </header>
      {children}
      <footer className="mx-auto flex max-w-[1440px] flex-col gap-4 border-t border-border/70 px-5 py-8 text-xs text-muted-foreground sm:px-8 lg:px-12">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <span className="font-mono-app text-[10px] uppercase tracking-[.16em]">ClearClause · Legal operations, clarified</span>
          <span className="flex items-center gap-1.5">
            <ShieldCheck size={13} className="text-primary" /> Raw file content is not stored
          </span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground/70 border-t border-border/50 pt-4">
          <Bot size={12} className="text-primary/50" />
          <span>Agentic RAG powered by Mistral-7B · GTE-small embeddings · FAISS + BM25 hybrid retrieval · 7 specialized AI agents</span>
        </div>
        <div className="text-[11px] text-muted-foreground/60">
          Platform creators: <span className="font-semibold text-foreground/70">Kirti Kumari</span> &amp; <span className="font-semibold text-foreground/70">Kushagra Srivastava</span>
        </div>
      </footer>
    </div>
  );
}

// ── upload panel ───────────────────────────────────────────────────────────

function UploadPanel({ onComplete }: { onComplete: (doc: AnalysisResult) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [filename, setFilename] = useState('');
  const [content, setContent] = useState('');
  const [mimeType, setMimeType] = useState('');
  const [size, setSize] = useState(0);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const ingestFile = (file: File) => {
    setFilename(file.name);
    setMimeType(file.type || 'application/octet-stream');
    setSize(file.size);
    setError('');
    file.text().then((text) => setContent(text.slice(0, 300_000))).catch(() => setContent(''));
  };

  const submit = async () => {
    if (!filename.trim() || content.length < 20 || loading) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/documents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: filename.trim(), mimeType, content, size }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Server error ${res.status}`);
      }
      const doc = await res.json() as AnalysisResult;
      onComplete(doc);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="relative overflow-hidden rounded-[22px] border border-primary/20 bg-[#e5efea] p-5 sm:p-7">
      <div className="absolute -right-14 -top-16 h-48 w-48 rounded-full border-[26px] border-[#cbded5]/60" />
      <div className="relative">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <div className="mb-2 flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.18em] text-primary">
              <Sparkles size={13} /> New analysis · 7 AI agents
            </div>
            <h2 className="font-display text-[29px] leading-[1.05] text-[#173c3b]">Make the fine print legible.</h2>
            <p className="mt-2 max-w-md text-sm leading-6 text-[#466d68]">
              Upload a contract and get a full agentic RAG analysis — red flags, green flags, risk scores, obligations, and negotiation advice.
            </p>
          </div>
          <FileCheck2 className="hidden text-primary/35 sm:block" size={42} strokeWidth={1} />
        </div>

        <button
          type="button"
          id="upload-dropzone"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) ingestFile(f); }}
          className={cn(
            'group flex w-full items-center gap-4 rounded-xl border border-dashed border-primary/35 bg-[#f6faf5]/75 px-4 py-4 text-left transition-all hover:border-primary hover:bg-[#f8fbf7]',
            dragging && 'border-primary bg-[#f8fbf7]',
          )}
        >
          <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground transition-transform group-hover:-translate-y-0.5">
            <UploadCloud size={20} />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-semibold text-[#234d49]">
              {filename || 'Choose a document to analyze'}
            </span>
            <span className="mt-0.5 block text-xs text-[#63817c]">
              {filename ? `${formatBytes(size)} · ready to review` : 'PDF, DOCX, or TXT · up to 20 MB'}
            </span>
          </span>
          <ChevronRight className="ml-auto shrink-0 text-primary/60" size={18} />
        </button>

        <input
          ref={inputRef}
          id="input-document-file"
          className="hidden"
          type="file"
          accept=".pdf,.doc,.docx,.txt,application/pdf,text/plain"
          onChange={(e: ChangeEvent<HTMLInputElement>) => { const f = e.target.files?.[0]; if (f) ingestFile(f); }}
        />

        {filename && (
          <div className="mt-4 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs text-[#4f706b]">
              <Check size={14} className="text-primary" /> Document attached securely
            </div>
            <button
              id="button-analyze-document"
              onClick={submit}
              disabled={loading || content.length < 20}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-all hover:-translate-y-0.5 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading
                ? <><Loader2 size={15} className="animate-spin" /> Analyzing with 7 agents…</>
                : <>Analyze document <ArrowUpRight size={15} /></>
              }
            </button>
          </div>
        )}

        {loading && (
          <div className="mt-4 rounded-lg border border-primary/20 bg-[#f0f7f3] p-3">
            <div className="flex items-center gap-2 text-xs text-primary font-medium mb-2">
              <Bot size={13} className="animate-pulse" /> Agentic RAG pipeline running…
            </div>
            <div className="grid grid-cols-2 gap-1 text-[10px] text-[#4f706b]">
              {['Summary Agent', 'Red Flag Detector', 'Green Flag Detector', 'Obligation Extractor', 'Comparison Agent', 'Risk Scorer', 'Negotiation Advisor'].map((a) => (
                <div key={a} className="flex items-center gap-1"><Zap size={9} className="text-primary/60" />{a}</div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 flex items-start gap-2 rounded-lg border border-[#e7b5ae] bg-[#fff5f2] p-3 text-xs leading-5 text-[#983d35]">
            <AlertCircle size={15} className="mt-0.5 shrink-0" /> {error}
          </div>
        )}

        <p className="mt-5 flex items-center gap-1.5 text-[11px] text-[#63817c]">
          <LockKeyhole size={12} /> Files processed for analysis; raw content not stored after review.
        </p>
      </div>
    </section>
  );
}

// ── library page ───────────────────────────────────────────────────────────

function Metric({ label, value, note, icon: Icon }: { label: string; value: string | number; note: string; icon: typeof FileText }) {
  return (
    <div className="rounded-2xl border border-border/80 bg-card p-5 transition-transform duration-300 hover:-translate-y-0.5">
      <div className="mb-7 flex items-start justify-between">
        <span className="font-mono-app text-[10px] uppercase tracking-[.15em] text-muted-foreground">{label}</span>
        <Icon size={17} strokeWidth={1.7} className="text-primary/70" />
      </div>
      <div className="font-display text-[38px] leading-none text-foreground">{value}</div>
      <div className="mt-2 text-xs text-muted-foreground">{note}</div>
    </div>
  );
}

function DocumentRow({ doc, onOpen }: { doc: LibraryDoc; onOpen: () => void }) {
  return (
    <button
      onClick={onOpen}
      className="group flex w-full items-center gap-4 border-b border-border/70 px-1 py-4 text-left transition-colors hover:bg-[#f4f1e8] sm:px-3 bg-transparent cursor-pointer"
    >
      <div className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-[#e7eee9] text-primary">
        <FileText size={18} strokeWidth={1.7} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-semibold text-foreground">{doc.filename}</div>
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
          <span>{doc.documentType || 'Legal document'}</span>
          <span className="text-border">·</span>
          <span>{formatDate(doc.createdAt)}</span>
          <span className="text-border">·</span>
          <span>{formatBytes(doc.size)}</span>
          {doc.overallScore !== undefined && (
            <><span className="text-border">·</span><span className="font-mono-app">Score: {doc.overallScore}/100</span></>
          )}
        </div>
      </div>
      <RiskBadge level={doc.riskLevel} compact />
      <ArrowUpRight size={16} className="hidden text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 sm:block" />
    </button>
  );
}

function LibraryPage({ library, onOpen, onAnalyzed }: {
  library: LibraryDoc[];
  onOpen: (id: string) => void;
  onAnalyzed: (doc: AnalysisResult) => void;
}) {
  const [search, setSearch] = useState('');
  const filtered = useMemo(
    () => library.filter((d) => d.filename.toLowerCase().includes(search.toLowerCase())),
    [library, search],
  );

  const highRisk = library.filter((d) => d.riskLevel === 'high').length;
  const thisWeek = library.filter((d) => {
    const created = new Date(d.createdAt);
    const weekAgo = new Date(Date.now() - 7 * 86400_000);
    return created >= weekAgo;
  }).length;

  return (
    <main className="mx-auto max-w-[1440px] px-5 pb-14 pt-10 sm:px-8 lg:px-12 lg:pt-14">
      <section className="mb-10 flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
        <div className="animate-rise">
          <div className="mb-4 flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.2em] text-primary">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" /> Legal workspace · Agentic RAG
          </div>
          <h1 className="max-w-2xl font-display text-[clamp(42px,6vw,72px)] leading-[.92] tracking-[-.025em]">
            Clarity for the<br />
            <em className="text-primary">clauses that count.</em>
          </h1>
          <p className="mt-5 max-w-lg text-[15px] leading-7 text-muted-foreground">
            7 specialized AI agents analyse your contracts using Retrieval-Augmented Generation — surfacing red flags, green flags, risk scores, and negotiation advice.
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground animate-rise animate-rise-delay-1">
          <span className="grid h-8 w-8 place-items-center rounded-full border border-border bg-card">
            <ShieldCheck size={15} className="text-primary" />
          </span>
          <span>
            <strong className="font-semibold text-foreground">Privacy-aware by default.</strong><br />
            Raw file content is not retained.
          </span>
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.02fr)_minmax(430px,.98fr)]">
        <div className="order-2 space-y-5 lg:order-1">
          <UploadPanel onComplete={onAnalyzed} />
          <section className="rounded-[22px] border border-border/80 bg-card p-5 sm:p-7">
            <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <div>
                <div className="flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.16em] text-muted-foreground">
                  <FolderOpen size={13} /> Your library
                </div>
                <h2 className="mt-2 font-display text-[27px]">Recent documents</h2>
              </div>
              {library.length > 0 && (
                <div className="relative">
                  <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input
                    id="input-search-documents"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Find a document"
                    className="h-9 w-full rounded-lg border border-border bg-background pl-9 pr-3 text-xs outline-none transition-colors placeholder:text-muted-foreground focus:border-primary sm:w-44"
                  />
                </div>
              )}
            </div>
            {filtered.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border bg-background/60 px-5 py-10 text-center">
                <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-[#e8f0eb] text-primary">
                  <BookOpen size={22} />
                </div>
                <h3 className="mt-4 text-sm font-semibold">
                  {search ? 'No matching documents' : 'Your library is ready'}
                </h3>
                <p className="mx-auto mt-1 max-w-xs text-xs leading-5 text-muted-foreground">
                  {search ? 'Try a different filename.' : 'Upload your first agreement above to begin a focused review.'}
                </p>
              </div>
            ) : (
              <div>
                {filtered.map((doc) => (
                  <DocumentRow key={doc.id} doc={doc} onOpen={() => onOpen(doc.id)} />
                ))}
              </div>
            )}
          </section>
        </div>

        <aside className="order-1 space-y-5 lg:order-2">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-2">
            <Metric label="Documents" value={library.length || '—'} note="in your library" icon={FileText} />
            <Metric label="This week" value={thisWeek || '—'} note="newly reviewed" icon={Clock3} />
            <Metric label="High risk" value={highRisk || '—'} note="need a closer look" icon={TriangleAlert} />
            <Metric label="Agents" value={7} note="AI agents running" icon={Bot} />
          </div>
          <div className="relative overflow-hidden rounded-2xl bg-[#173c3b] p-6 text-[#eff5ed]">
            <div className="absolute -bottom-10 -right-8 h-32 w-32 rounded-full border-[18px] border-[#3d6c65]/60" />
            <Info size={18} className="mb-10 text-[#e5b873]" />
            <h3 className="relative max-w-[230px] font-display text-[26px] leading-[1.05]">A second set of eyes, not a final answer.</h3>
            <p className="relative mt-3 max-w-[270px] text-xs leading-5 text-[#b7ceca]">
              ClearClause uses Agentic RAG with 7 specialized AI agents trained on legal knowledge to help you spot what deserves attention. It does not replace advice from a qualified legal professional.
            </p>
          </div>
          <div className="rounded-2xl border border-border/80 bg-card p-5">
            <div className="flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.16em] text-muted-foreground mb-4">
              <Bot size={13} /> AI pipeline
            </div>
            <div className="space-y-2">
              {['Red Flag Detector', 'Green Flag Detector', 'Summary Agent', 'Obligation Extractor', 'Comparison Agent', 'Risk Scorer', 'Negotiation Advisor'].map((agent, i) => (
                <div key={agent} className="flex items-center gap-2 text-xs">
                  <span className="grid h-5 w-5 place-items-center rounded bg-[#e8f0eb] font-mono-app text-[9px] text-primary">{i + 1}</span>
                  <span className="text-foreground/80">{agent}</span>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}

// ── detail page components ─────────────────────────────────────────────────

function Collapsible({ title, count, children, defaultOpen = true, icon: Icon }: {
  title: string; count?: number; children: ReactNode; defaultOpen?: boolean; icon: typeof FileText;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="rounded-2xl border border-border/80 bg-card">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between p-6 sm:p-8 bg-transparent border-0 cursor-pointer text-left"
      >
        <div>
          <div className="flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.16em] text-muted-foreground">
            <Icon size={13} />
            {title}
            {count !== undefined && (
              <span className="ml-auto font-mono-app text-[11px] text-muted-foreground">
                {count.toString().padStart(2, '0')} items
              </span>
            )}
          </div>
        </div>
        {open ? <ChevronUp size={16} className="text-muted-foreground" /> : <ChevronDown size={16} className="text-muted-foreground" />}
      </button>
      {open && <div className="px-6 pb-6 sm:px-8 sm:pb-8 -mt-2">{children}</div>}
    </section>
  );
}

function RedFlagCard({ flag, index }: { flag: RedFlag; index: number }) {
  const color = flag.severity === 'high' ? 'border-l-[#b84e43]' : flag.severity === 'medium' ? 'border-l-[#ce8d34]' : 'border-l-[#4f9984]';
  return (
    <article className={cn('rounded-xl border border-border/80 border-l-[3px] bg-card p-5 transition-transform duration-300 hover:-translate-y-0.5', color)}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2">
          <XCircle size={15} className="text-[#983d35] shrink-0 mt-0.5" />
          <h3 className="text-sm font-semibold">{flag.title}</h3>
        </div>
        <RiskBadge level={flag.severity} compact />
      </div>
      {flag.category && <div className="mt-1 font-mono-app text-[9px] uppercase tracking-wider text-muted-foreground">{flag.category}</div>}
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{flag.detail}</p>
      {flag.excerpt && (
        <blockquote className="mt-4 border-l border-border pl-3 font-display text-[15px] italic leading-6 text-foreground/75">"{flag.excerpt}"</blockquote>
      )}
      {flag.recommendation && (
        <div className="mt-3 flex items-start gap-2 rounded-lg bg-[#fff8f0] border border-[#edcf9d] p-3 text-xs leading-5 text-[#9a651d]">
          <Lightbulb size={13} className="mt-0.5 shrink-0" /> {flag.recommendation}
        </div>
      )}
    </article>
  );
}

function GreenFlagCard({ flag, index }: { flag: GreenFlag; index: number }) {
  return (
    <article className="rounded-xl border border-border/80 border-l-[3px] border-l-[#4f9984] bg-card p-5 transition-transform duration-300 hover:-translate-y-0.5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={15} className="text-[#286a59] shrink-0 mt-0.5" />
          <h3 className="text-sm font-semibold">{flag.title}</h3>
        </div>
        {flag.strength && (
          <span className={cn(
            'rounded-full border px-2 py-0.5 font-mono-app text-[9px] uppercase tracking-wider',
            flag.strength === 'strong' ? 'bg-[#dceee7] text-[#286a59] border-[#b9dccc]' : 'bg-[#e8f4f0] text-[#4f9984] border-[#c8e4dc]',
          )}>{flag.strength}</span>
        )}
      </div>
      {flag.category && <div className="mt-1 font-mono-app text-[9px] uppercase tracking-wider text-muted-foreground">{flag.category}</div>}
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{flag.detail}</p>
      {flag.excerpt && (
        <blockquote className="mt-4 border-l border-border pl-3 font-display text-[15px] italic leading-6 text-foreground/75">"{flag.excerpt}"</blockquote>
      )}
    </article>
  );
}

function ObligationRow({ obligation, index }: { obligation: Obligation; index: number }) {
  return (
    <div className="grid gap-2 border-b border-border/70 py-4 last:border-0 sm:grid-cols-[1fr_1.6fr_1fr_auto] sm:items-center">
      <div className="text-xs font-semibold text-foreground">{obligation.party}</div>
      <div className="text-sm text-muted-foreground">{obligation.action}</div>
      <div className="text-xs text-muted-foreground">
        <span className="font-mono-app text-[9px] uppercase tracking-wider text-muted-foreground/70">Timing </span>
        {obligation.timing}
      </div>
      <span className={cn(
        'w-fit rounded-full px-2 py-1 font-mono-app text-[9px] uppercase tracking-wider',
        obligation.status === 'unclear' ? 'bg-[#fff0d7] text-[#9a651d]' :
          obligation.status === 'ongoing' ? 'bg-[#dce9f2] text-[#3c6681]' :
            'bg-[#dceee7] text-[#286a59]',
      )}>{obligation.status}</span>
    </div>
  );
}

function ComparisonRow({ item }: { item: Comparison }) {
  const statusIcon = item.status === 'missing' || item.deviation_level === 'critical'
    ? <XCircle size={14} className="text-[#983d35] shrink-0" />
    : item.status === 'present_unusual' || item.deviation_level === 'significant'
      ? <AlertCircle size={14} className="text-[#9a651d] shrink-0" />
      : <CheckCircle2 size={14} className="text-[#286a59] shrink-0" />;

  return (
    <div className="flex items-start gap-3 border-b border-border/70 py-4 last:border-0">
      <div className="mt-0.5">{statusIcon}</div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold text-foreground">{item.clause_type}</div>
        <div className="mt-1 text-xs text-muted-foreground leading-5">{item.finding}</div>
        {item.deviation_level !== 'none' && (
          <div className="mt-1 text-[10px] text-muted-foreground/70 font-mono-app uppercase tracking-wide">
            Standard: {item.standard_practice}
          </div>
        )}
      </div>
      <span className={cn(
        'shrink-0 rounded-full px-2 py-0.5 font-mono-app text-[9px] uppercase tracking-wider',
        item.deviation_level === 'critical' ? 'bg-[#f8e1dc] text-[#983d35]' :
          item.deviation_level === 'significant' ? 'bg-[#fff0d7] text-[#9a651d]' :
            item.deviation_level === 'minor' ? 'bg-[#dce9f2] text-[#3c6681]' :
              'bg-[#dceee7] text-[#286a59]',
      )}>{item.deviation_level === 'none' ? 'ok' : item.deviation_level}</span>
    </div>
  );
}

function NegotiationCard({ item }: { item: Negotiation }) {
  const priorityStyle = item.priority === 'must_negotiate'
    ? 'bg-[#f8e1dc] text-[#983d35] border-[#e9b9b0]'
    : item.priority === 'should_negotiate'
      ? 'bg-[#fff0d7] text-[#9a651d] border-[#edcf9d]'
      : 'bg-[#dce9f2] text-[#3c6681] border-[#b8d0e0]';

  return (
    <article className="rounded-xl border border-border/80 bg-card p-5 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <MessageSquare size={14} className="text-primary shrink-0 mt-0.5" />
          <h3 className="text-sm font-semibold">{item.original_issue}</h3>
        </div>
        <span className={cn('shrink-0 rounded-full border px-2 py-0.5 font-mono-app text-[9px] uppercase tracking-wider', priorityStyle)}>
          {item.priority.replace(/_/g, ' ')}
        </span>
      </div>
      <div className="space-y-2 text-xs leading-5">
        <div className="rounded-lg bg-[#e8f0eb] p-3">
          <div className="font-semibold text-[#234d49] mb-1">Suggested change</div>
          <div className="text-[#4f706b]">{item.suggested_change}</div>
        </div>
        <div className="rounded-lg bg-[#f0f5fa] p-3">
          <div className="font-semibold text-[#2a4a60] mb-1">Negotiation strategy</div>
          <div className="text-[#3c6681]">{item.negotiation_strategy}</div>
        </div>
        <div className="rounded-lg bg-muted p-3">
          <div className="font-semibold text-foreground/70 mb-1">Fallback position</div>
          <div className="text-muted-foreground">{item.fallback_position}</div>
        </div>
      </div>
    </article>
  );
}

function RiskDimensionBar({ dim }: { dim: RiskDimension }) {
  const color = dim.score <= 35 ? '#286a59' : dim.score <= 65 ? '#9a651d' : '#983d35';
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-foreground/80">{dim.dimension}</span>
        <span className="font-mono-app font-bold" style={{ color }}>{dim.score}</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${dim.score}%`, backgroundColor: color }} />
      </div>
      <p className="text-[10px] text-muted-foreground leading-4">{dim.rationale}</p>
    </div>
  );
}

function AgentLogPanel({ log }: { log: AgentLogEntry[] }) {
  const [open, setOpen] = useState(false);
  if (!log || log.length === 0) return null;
  return (
    <div className="rounded-2xl border border-border/80 bg-card overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between p-5 bg-transparent border-0 cursor-pointer text-left"
      >
        <div className="flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.16em] text-muted-foreground">
          <Bot size={13} /> Agent execution log
        </div>
        {open ? <ChevronUp size={14} className="text-muted-foreground" /> : <ChevronDown size={14} className="text-muted-foreground" />}
      </button>
      {open && (
        <div className="px-5 pb-5 space-y-2">
          {log.map((entry, i) => (
            <div key={i} className="flex items-center gap-3 text-xs border-b border-border/50 pb-2 last:border-0">
              <span className="font-mono-app text-primary/60 w-4 shrink-0">{i + 1}</span>
              <span className="font-semibold text-foreground/80 w-32 shrink-0">{entry.agent}</span>
              <span className="text-muted-foreground flex-1">{entry.result}</span>
              <span className="font-mono-app text-muted-foreground/60 shrink-0">{entry.duration_ms}ms</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── detail page ────────────────────────────────────────────────────────────

function DocumentPage({ doc, onBack }: { doc: AnalysisResult; onBack: () => void }) {
  const [activeTab, setActiveTab] = useState<'red' | 'green'>('red');
  const tabs = [
    { id: 'red' as const, label: `Red Flags (${doc.redFlags?.length ?? 0})`, icon: XCircle, color: 'text-[#983d35]' },
    { id: 'green' as const, label: `Green Flags (${doc.greenFlags?.length ?? 0})`, icon: CheckCircle2, color: 'text-[#286a59]' },
  ];

  return (
    <main className="mx-auto max-w-[1440px] px-5 pb-16 pt-8 sm:px-8 lg:px-12">
      <button
        onClick={onBack}
        className="inline-flex items-center gap-2 text-xs font-medium text-muted-foreground transition-colors hover:text-primary bg-transparent border-0 cursor-pointer p-0"
      >
        <ArrowLeft size={15} /> Back to library
      </button>

      <header className="mt-8 flex flex-col justify-between gap-7 border-b border-border/80 pb-8 md:flex-row md:items-end">
        <div className="animate-rise">
          <div className="mb-4 flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.17em] text-primary">
            <FileText size={13} /> Document analysis · Agentic RAG
          </div>
          <h1 className="max-w-3xl break-words font-display text-[clamp(38px,5.4vw,68px)] leading-[.94]">{doc.filename}</h1>
          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span>{doc.documentType || 'Legal document'}</span>
            <span className="text-border">·</span>
            <span>Added {formatDate(doc.createdAt)}</span>
            <span className="text-border">·</span>
            <span>{formatBytes(doc.size)}</span>
            {doc.parties?.length > 0 && (
              <><span className="text-border">·</span><span>Parties: {doc.parties.slice(0, 3).join(', ')}</span></>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-3 animate-rise animate-rise-delay-1">
          <RiskBadge level={doc.riskLevel} />
          <ScoreMeter score={doc.overallScore} />
          <span className="rounded-full border border-border px-3 py-1.5 font-mono-app text-[10px] uppercase tracking-wider text-muted-foreground">
            {doc.agentsCompleted?.length ?? 7}/7 agents complete
          </span>
        </div>
      </header>

      <div className="mt-7 grid gap-6 lg:grid-cols-[minmax(0,1.28fr)_minmax(290px,.72fr)]">
        <div className="space-y-6">

          {/* summary */}
          <section className="rounded-2xl border border-border/80 bg-card p-6 sm:p-8">
            <div className="mb-5 flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.16em] text-primary">
              <Sparkles size={13} /> Plain-language brief
            </div>
            <p className="max-w-3xl font-display text-[26px] leading-[1.2] text-foreground sm:text-[31px]">{doc.summary}</p>
            <div className="mt-7 flex items-start gap-2 border-t border-border/70 pt-4 text-xs leading-5 text-muted-foreground">
              <Info size={14} className="mt-0.5 shrink-0 text-primary" />
              This analysis is informational and is not legal advice. For decisions with legal or financial impact, consult a qualified professional.
            </div>
          </section>

          {/* red & green flags tabbed */}
          <section className="rounded-2xl border border-border/80 bg-card p-6 sm:p-8">
            <div className="mb-5 flex gap-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    'inline-flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold transition-all border-0 cursor-pointer',
                    activeTab === tab.id
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80',
                  )}
                >
                  <tab.icon size={13} />
                  {tab.label}
                </button>
              ))}
            </div>

            {activeTab === 'red' && (
              <>
                <div className="mb-4 flex items-end justify-between gap-4">
                  <h2 className="font-display text-[29px]">What deserves a closer look</h2>
                  <span className="font-mono-app text-[11px] text-muted-foreground">{(doc.redFlags?.length ?? 0).toString().padStart(2, '0')} findings</span>
                </div>
                {doc.redFlags?.length ? (
                  <div className="space-y-3">
                    {doc.redFlags.map((flag, i) => <RedFlagCard key={i} flag={flag} index={i} />)}
                  </div>
                ) : (
                  <div className="rounded-xl bg-[#e8f0eb] p-5 text-sm text-[#286a59]">No material red flags were identified in this review.</div>
                )}
              </>
            )}

            {activeTab === 'green' && (
              <>
                <div className="mb-4 flex items-end justify-between gap-4">
                  <h2 className="font-display text-[29px]">Protective clauses found</h2>
                  <span className="font-mono-app text-[11px] text-muted-foreground">{(doc.greenFlags?.length ?? 0).toString().padStart(2, '0')} findings</span>
                </div>
                {doc.greenFlags?.length ? (
                  <div className="space-y-3">
                    {doc.greenFlags.map((flag, i) => <GreenFlagCard key={i} flag={flag} index={i} />)}
                  </div>
                ) : (
                  <div className="rounded-xl bg-muted p-5 text-sm text-muted-foreground">No strong protective clauses were identified.</div>
                )}
              </>
            )}
          </section>

          {/* obligations */}
          <Collapsible title="Commitments" count={doc.obligations?.length} icon={Check} defaultOpen={true}>
            <h2 className="font-display text-[29px] mb-4">Who needs to do what</h2>
            {doc.obligations?.length ? (
              <div>{doc.obligations.map((o, i) => <ObligationRow key={i} obligation={o} index={i} />)}</div>
            ) : (
              <div className="rounded-xl bg-muted p-5 text-sm text-muted-foreground">No explicit obligations were extracted.</div>
            )}
          </Collapsible>

          {/* negotiations */}
          {(doc.negotiations?.length ?? 0) > 0 && (
            <Collapsible title="Negotiation Advice" count={doc.negotiations?.length} icon={MessageSquare} defaultOpen={false}>
              <h2 className="font-display text-[29px] mb-4">How to push back</h2>
              <div className="space-y-4">
                {doc.negotiations.map((n, i) => <NegotiationCard key={i} item={n} />)}
              </div>
            </Collapsible>
          )}

          {/* comparison */}
          {(doc.comparisons?.length ?? 0) > 0 && (
            <Collapsible title="Standard Comparison" count={doc.comparisons?.length} icon={GitCompare} defaultOpen={false}>
              <h2 className="font-display text-[29px] mb-4">vs. standard templates</h2>
              <div>{doc.comparisons.map((c, i) => <ComparisonRow key={i} item={c} />)}</div>
            </Collapsible>
          )}

          {/* agent log */}
          <AgentLogPanel log={doc.executionLog} />
        </div>

        <aside className="space-y-6">
          {/* key terms */}
          <section className="rounded-2xl border border-border/80 bg-card p-6">
            <div className="flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.16em] text-muted-foreground">
              <BookOpen size={13} /> Key terms
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              {doc.keyTerms?.length
                ? doc.keyTerms.map((term, i) => (
                  <span key={i} className="rounded-lg bg-[#e8f0eb] px-3 py-2 text-xs font-medium text-[#286a59]">{term}</span>
                ))
                : <span className="text-sm text-muted-foreground">No key terms extracted.</span>
              }
            </div>
          </section>

          {/* risk score dimensions */}
          {(doc.riskScores?.dimensions?.length ?? 0) > 0 && (
            <section className="rounded-2xl border border-border/80 bg-card p-6">
              <div className="flex items-center gap-2 font-mono-app text-[10px] uppercase tracking-[.16em] text-muted-foreground mb-4">
                <BarChart3 size={13} /> Risk dimensions
              </div>
              <div className="space-y-4">
                {doc.riskScores.dimensions.map((dim, i) => <RiskDimensionBar key={i} dim={dim} />)}
              </div>
              {doc.riskScores.explanation && (
                <p className="mt-4 text-xs leading-5 text-muted-foreground border-t border-border/70 pt-4">{doc.riskScores.explanation}</p>
              )}
            </section>
          )}

          {/* quick stats */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-xl border border-[#e9b9b0] bg-[#fff5f2] p-4 text-center">
              <div className="font-display text-3xl text-[#983d35]">{doc.redFlags?.length ?? 0}</div>
              <div className="mt-1 font-mono-app text-[9px] uppercase tracking-wide text-[#983d35]">Red flags</div>
            </div>
            <div className="rounded-xl border border-[#b9dccc] bg-[#eaf4ef] p-4 text-center">
              <div className="font-display text-3xl text-[#286a59]">{doc.greenFlags?.length ?? 0}</div>
              <div className="mt-1 font-mono-app text-[9px] uppercase tracking-wide text-[#286a59]">Green flags</div>
            </div>
          </div>

          {/* cta */}
          <section className="rounded-2xl bg-[#173c3b] p-6 text-[#eff5ed]">
            <LockKeyhole size={18} className="text-[#e5b873]" />
            <h2 className="mt-12 font-display text-[27px] leading-[1.05]">Keep your next move close.</h2>
            <p className="mt-3 text-xs leading-5 text-[#b7ceca]">Use these findings as a briefing before a conversation with your counsel or team.</p>
            <button
              onClick={onBack}
              className="mt-5 inline-flex items-center gap-2 text-xs font-semibold text-[#e5b873] transition-colors hover:text-[#f1ce8d] bg-transparent border-0 cursor-pointer p-0"
            >
              Review another document <ArrowUpRight size={14} />
            </button>
          </section>
        </aside>
      </div>
    </main>
  );
}

// ── root app ───────────────────────────────────────────────────────────────

export default function App() {
  const [view, updateView] = useState<View>('library');
  const [selectedDoc, updateSelectedDoc] = useState<AnalysisResult | null>(null);
  const [library, setLibrary] = useState<LibraryDoc[]>([]);

  setView = updateView;
  setSelectedDoc = updateSelectedDoc;

  const handleAnalyzed = (doc: AnalysisResult) => {
    setLibrary((prev) => {
      const exists = prev.find((d) => d.id === doc.id);
      if (exists) return prev;
      return [{
        id: doc.id,
        filename: doc.filename,
        size: doc.size,
        documentType: doc.documentType,
        riskLevel: doc.riskLevel,
        overallScore: doc.overallScore,
        createdAt: doc.createdAt,
      }, ...prev];
    });
    updateSelectedDoc(doc);
    updateView('detail');
  };

  const handleOpen = (id: string) => {
    const cached = library.find((d) => d.id === id) as unknown as AnalysisResult | undefined;
    if (cached) {
      updateSelectedDoc(cached as unknown as AnalysisResult);
      updateView('detail');
    }
  };

  return (
    <Shell onHome={() => updateView('library')}>
      {view === 'library' && (
        <LibraryPage library={library} onOpen={handleOpen} onAnalyzed={handleAnalyzed} />
      )}
      {view === 'detail' && selectedDoc && (
        <DocumentPage doc={selectedDoc} onBack={() => updateView('library')} />
      )}
    </Shell>
  );
}