const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"

export type RoundSummary = {
  round: number
  question: string
  gt: string
  pred: string
  acc: number
  strategy: string
  consensus_option: string
  consensus_ratio: number
  high_threshold: number
  mid_threshold: number
  correct_tendency: boolean
  tokens: number
  answer_change_rate: number
  correction_rate: number
  wrong_change_rate: number
  two_round_same_rate: number
  graph: Record<string, string>
  secondary_graph: Record<string, string>
}

export type ExperimentSummary = {
  experiment_id: string
  result_dir: string
  mode: string
  path: string
  trace_path: string
  summary_path: string
  comparison_path: string
  round_count: number
  max_rounds: number
  final_accuracy: number
  total_tokens: number
  average_similarity: number
  strategy_distribution: Record<string, number>
  question_preview: string
  summary: Record<string, unknown>
  latest_round: RoundSummary | null
  rounds: RoundSummary[]
  search_blob: string
}

export type ExperimentDetail = ExperimentSummary & {
  trace: Record<string, unknown>[]
}

export type RoundDetail = {
  experiment_id: string
  round_number: number
  data: Record<string, unknown>
}

async function requestJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    headers: {
      Accept: "application/json",
    },
  })

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status} ${response.statusText}`)
  }

  return response.json() as Promise<T>
}

export async function listExperiments(query?: string, mode?: string) {
  const params = new URLSearchParams()

  if (query) {
    params.set("query", query)
  }

  if (mode && mode !== "all") {
    params.set("mode", mode)
  }

  const suffix = params.toString() ? `?${params.toString()}` : ""
  return requestJson<{ items: ExperimentSummary[]; total: number }>(`/api/experiments${suffix}`)
}

export async function getExperiment(experimentId: string) {
  return requestJson<ExperimentDetail>(`/api/experiments/${encodeURIComponent(experimentId)}`)
}

export async function getExperimentRounds(experimentId: string) {
  return requestJson<{ experiment_id: string; rounds: RoundSummary[]; summary: Record<string, unknown> }>(
    `/api/experiments/${encodeURIComponent(experimentId)}/rounds`
  )
}

export async function getRoundDetail(experimentId: string, roundNumber: number) {
  return requestJson<RoundDetail>(`/api/experiments/${encodeURIComponent(experimentId)}/rounds/${roundNumber}`)
}

export async function searchRounds(experimentId: string, query: string) {
  const params = new URLSearchParams({ query })
  return requestJson<{ experiment_id: string; query: string; matches: RoundSummary[] }>(
    `/api/experiments/${encodeURIComponent(experimentId)}/search?${params.toString()}`
  )
}

export async function getHealth() {
  return requestJson<{ status: string; experiment_root: string }>("/api/health")
}

export function buildExperimentHref(experimentId: string) {
  return `/history/${encodeURIComponent(experimentId)}`
}

export function buildRoundHref(experimentId: string, roundNumber: number) {
  return `/history/${encodeURIComponent(experimentId)}/rounds/${roundNumber}`
}

export function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

export function formatTokenCount(value: number | null | undefined) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "0"
  }

  return value.toLocaleString()
}

export function formatModeLabel(mode: string) {
  const text = mode.replaceAll("_", " ")

  const map: Record<string, string> = {
    dissimilar: "低相似",
    similar: "高相似",
    random: "随机",
    mixed: "混合",
    "dissimilar then similar": "先低相似后高相似",
    hybrid: "混合策略",
    unknown: "未知",
    loading: "加载中",
  }

  return map[text] ?? text
}