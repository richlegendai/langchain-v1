import { CheckCircle2, Database, FileCheck2, RefreshCw, Send, Terminal } from "lucide-react";
import type { Candidate, QualityCheck } from "./api";

export type Provider = "codex" | "claude" | "gemini";
export type RequestState = "idle" | "loading" | "error" | "ready";

type HeaderProps = {
  readonly serverState: RequestState;
};

type InputPanelProps = {
  readonly topic: string;
  readonly keywords: string;
  readonly channel: string;
  readonly provider: Provider;
  readonly serverState: RequestState;
  readonly errorMessage: string;
  readonly onTopicChange: (value: string) => void;
  readonly onKeywordsChange: (value: string) => void;
  readonly onChannelChange: (value: string) => void;
  readonly onProviderChange: (value: Provider) => void;
  readonly onGenerate: () => void;
};

type CandidatePanelProps = {
  readonly candidates: readonly Candidate[];
  readonly selectedCandidateId: string | null;
  readonly onSelect: (candidate: Candidate) => void;
};

type EditorPanelProps = {
  readonly tone: string;
  readonly revisionRequest: string;
  readonly serverState: RequestState;
  readonly onToneChange: (value: string) => void;
  readonly onRevisionRequestChange: (value: string) => void;
  readonly onRevise: () => void;
};

type PreviewPanelProps = {
  readonly body: string;
};

type ChecksPanelProps = {
  readonly checks: readonly QualityCheck[];
};

type PublishPanelProps = {
  readonly serverState: RequestState;
  readonly savedPath: string;
  readonly searchSummary: readonly string[];
  readonly onApprove: () => void;
};

export function Header({ serverState }: HeaderProps) {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Content RAG Desktop</p>
        <h1>콘텐츠 생성, 수정, 검수, 발행 준비</h1>
      </div>
      <div className={`status-pill ${serverState}`}>
        <Terminal size={16} />
        <span>{serverState}</span>
      </div>
    </header>
  );
}

export function InputPanel(props: InputPanelProps) {
  return (
    <section className="panel input-panel">
      <h2>입력</h2>
      <label>
        주제
        <input value={props.topic} onChange={(event) => props.onTopicChange(event.target.value)} />
      </label>
      <label>
        키워드
        <input
          value={props.keywords}
          onChange={(event) => props.onKeywordsChange(event.target.value)}
        />
      </label>
      <div className="field-row">
        <label>
          채널
          <select
            value={props.channel}
            onChange={(event) => props.onChannelChange(event.target.value)}
          >
            <option value="blog">blog</option>
            <option value="sns">sns</option>
            <option value="newsletter">newsletter</option>
          </select>
        </label>
        <label>
          provider
          <select
            value={props.provider}
            onChange={(event) => props.onProviderChange(parseProvider(event.target.value))}
          >
            <option value="codex">codex</option>
            <option value="claude">claude</option>
            <option value="gemini">gemini</option>
          </select>
        </label>
      </div>
      <button
        className="primary-button"
        disabled={props.serverState === "loading"}
        onClick={props.onGenerate}
        type="button"
      >
        <Send size={16} />
        후보 생성
      </button>
      {props.errorMessage.length > 0 ? <p className="error-text">{props.errorMessage}</p> : null}
    </section>
  );
}

export function CandidatePanel(props: CandidatePanelProps) {
  return (
    <section className="panel candidates-panel">
      <h2>후보</h2>
      <div className="candidate-list">
        {props.candidates.map((candidate) => (
          <button
            className={
              candidate.id === props.selectedCandidateId ? "candidate selected" : "candidate"
            }
            key={candidate.id}
            onClick={() => props.onSelect(candidate)}
            type="button"
          >
            <strong>{candidate.title}</strong>
            <span>{candidate.summary}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

export function EditorPanel(props: EditorPanelProps) {
  return (
    <section className="panel editor-panel">
      <div className="section-title">
        <h2>수정</h2>
        <RefreshCw size={18} />
      </div>
      <label>
        말투
        <input value={props.tone} onChange={(event) => props.onToneChange(event.target.value)} />
      </label>
      <label>
        수정 요청
        <textarea
          value={props.revisionRequest}
          onChange={(event) => props.onRevisionRequestChange(event.target.value)}
        />
      </label>
      <button
        className="secondary-button"
        disabled={props.serverState === "loading"}
        onClick={props.onRevise}
        type="button"
      >
        수정본 생성
      </button>
    </section>
  );
}

export function PreviewPanel({ body }: PreviewPanelProps) {
  return (
    <section className="panel preview-panel">
      <div className="section-title">
        <h2>본문</h2>
        <Database size={18} />
      </div>
      <pre>{body || "후보를 생성하면 본문이 표시됩니다."}</pre>
    </section>
  );
}

export function ChecksPanel({ checks }: ChecksPanelProps) {
  return (
    <section className="panel checks-panel">
      <div className="section-title">
        <h2>검수</h2>
        <CheckCircle2 size={18} />
      </div>
      <div className="check-list">
        {checks.map((check) => (
          <div className={`check-item ${check.status}`} key={check.name}>
            <strong>{check.name}</strong>
            <span>{check.status}</span>
            <p>{check.detail}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function PublishPanel(props: PublishPanelProps) {
  return (
    <section className="panel publish-panel">
      <div className="section-title">
        <h2>발행 준비</h2>
        <FileCheck2 size={18} />
      </div>
      <button
        className="primary-button"
        disabled={props.serverState === "loading"}
        onClick={props.onApprove}
        type="button"
      >
        Markdown 저장
      </button>
      <p className="saved-path">{props.savedPath || "저장 전"}</p>
      <div className="search-summary">
        {props.searchSummary.map((summary) => (
          <p key={summary}>{summary.slice(0, 140)}</p>
        ))}
      </div>
    </section>
  );
}

function parseProvider(value: string): Provider {
  switch (value) {
    case "codex":
      return "codex";
    case "claude":
      return "claude";
    case "gemini":
      return "gemini";
    default:
      throw new Error(`unknown provider: ${value}`);
  }
}
