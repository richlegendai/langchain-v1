import { invoke } from "@tauri-apps/api/core";
import { useEffect, useMemo, useState } from "react";
import type { Candidate, QualityCheck } from "./api";
import { approveDraft, generateContent, reviseContent } from "./api";
import {
  CandidatePanel,
  ChecksPanel,
  EditorPanel,
  Header,
  InputPanel,
  PreviewPanel,
  type Provider,
  PublishPanel,
  type RequestState,
} from "./components";

declare global {
  interface Window {
    readonly __TAURI_INTERNALS__?: unknown;
  }
}

export function App() {
  const [topic, setTopic] = useState("로컬 RAG로 콘텐츠 초안 만들기");
  const [keywords, setKeywords] = useState("RAG, CTA, 검수");
  const [channel, setChannel] = useState("blog");
  const [provider, setProvider] = useState<Provider>("codex");
  const [tone, setTone] = useState("차분하고 실무적인 말투");
  const [revisionRequest, setRevisionRequest] = useState("CTA를 더 자연스럽게 보강해줘");
  const [draftId, setDraftId] = useState<number | null>(null);
  const [candidates, setCandidates] = useState<readonly Candidate[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [checks, setChecks] = useState<readonly QualityCheck[]>([]);
  const [searchSummary, setSearchSummary] = useState<readonly string[]>([]);
  const [currentBody, setCurrentBody] = useState("");
  const [savedPath, setSavedPath] = useState("");
  const [serverState, setServerState] = useState<RequestState>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (window.__TAURI_INTERNALS__ === undefined) {
      setServerState("ready");
      return;
    }
    invoke("start_agent_server")
      .then(() => setServerState("ready"))
      .catch((error: unknown) => {
        setErrorMessage(error instanceof Error ? error.message : String(error));
        setServerState("error");
      });
  }, []);

  const parsedKeywords = useMemo(
    () =>
      keywords
        .split(",")
        .map((keyword) => keyword.trim())
        .filter((keyword) => keyword.length > 0),
    [keywords],
  );

  async function handleGenerate(): Promise<void> {
    setServerState("loading");
    setErrorMessage("");
    try {
      const result = await generateContent({ topic, keywords: parsedKeywords, channel, provider });
      const firstCandidate = result.candidates[0];
      setDraftId(result.draft_id);
      setCandidates(result.candidates);
      setSelectedCandidateId(firstCandidate?.id ?? null);
      setCurrentBody(firstCandidate?.body ?? "");
      setSearchSummary(result.search_summary);
      setChecks(result.quality_checks);
      setServerState("ready");
    } catch (error: unknown) {
      handleError(error);
    }
  }

  async function handleRevise(): Promise<void> {
    if (draftId === null || selectedCandidateId === null) {
      setErrorMessage("수정할 후보를 먼저 생성하고 선택해야 합니다.");
      setServerState("error");
      return;
    }
    setServerState("loading");
    setErrorMessage("");
    try {
      const result = await reviseContent({
        draft_id: draftId,
        candidate_id: selectedCandidateId,
        tone,
        revision_request: revisionRequest,
      });
      setCurrentBody(result.revised_body);
      setChecks(result.quality_checks);
      setServerState("ready");
    } catch (error: unknown) {
      handleError(error);
    }
  }

  async function handleApprove(): Promise<void> {
    if (draftId === null) {
      setErrorMessage("저장할 초안이 없습니다.");
      setServerState("error");
      return;
    }
    setServerState("loading");
    setErrorMessage("");
    try {
      const result = await approveDraft(draftId);
      setSavedPath(result.saved_path);
      setServerState("ready");
    } catch (error: unknown) {
      handleError(error);
    }
  }

  function handleError(error: unknown): void {
    setErrorMessage(error instanceof Error ? error.message : String(error));
    setServerState("error");
  }

  function handleCandidateSelect(candidate: Candidate): void {
    setSelectedCandidateId(candidate.id);
    setCurrentBody(candidate.body);
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <Header serverState={serverState} />
        <div className="layout-grid">
          <InputPanel
            channel={channel}
            errorMessage={errorMessage}
            keywords={keywords}
            onChannelChange={setChannel}
            onGenerate={handleGenerate}
            onKeywordsChange={setKeywords}
            onProviderChange={setProvider}
            onTopicChange={setTopic}
            provider={provider}
            serverState={serverState}
            topic={topic}
          />
          <CandidatePanel
            candidates={candidates}
            onSelect={handleCandidateSelect}
            selectedCandidateId={selectedCandidateId}
          />
          <EditorPanel
            onRevise={handleRevise}
            onRevisionRequestChange={setRevisionRequest}
            onToneChange={setTone}
            revisionRequest={revisionRequest}
            serverState={serverState}
            tone={tone}
          />
          <PreviewPanel body={currentBody} />
          <ChecksPanel checks={checks} />
          <PublishPanel
            onApprove={handleApprove}
            savedPath={savedPath}
            searchSummary={searchSummary}
            serverState={serverState}
          />
        </div>
      </section>
    </main>
  );
}
