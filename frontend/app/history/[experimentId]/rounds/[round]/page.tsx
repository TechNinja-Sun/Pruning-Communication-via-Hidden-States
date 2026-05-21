"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import {
  ArrowLeft,
  Copy,
  Database,
  FileJson,
  GitBranch,
  Layers3,
  Sparkles,
  Target,
  Timer,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { buildExperimentHref, formatModeLabel, formatPercent, formatTokenCount, getRoundDetail } from "@/lib/experiment-api"

export default function RoundDetailPage() {
  const params = useParams<{ experimentId: string; round: string }>()
  const experimentId = decodeURIComponent(params.experimentId)
  const roundNumber = Number(params.round)

  const [payload, setPayload] = useState<Record<string, any> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const load = async () => {
      try {
        setLoading(true)
        const response = await getRoundDetail(experimentId, roundNumber)
        if (mounted) {
          setPayload(response.data)
          setError(null)
        }
      } catch (reason) {
        if (mounted) {
          setError(reason instanceof Error ? reason.message : "加载轮次详情失败")
        }
      } finally {
        if (mounted) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      mounted = false
    }
  }, [experimentId, roundNumber])

  const roundMetrics = useMemo(() => {
    if (!payload) {
      return null
    }

    const strategy = payload.hybrid_strategy as Record<string, any> | undefined
    const tokens = payload.tokens as Record<string, { first: number; final: number }> | undefined
    const firstRound = payload.first_round_answers as Record<string, { model: string; answer: string; option: string; token_count: number }> | undefined
    const secondRound = payload.second_round_answers as Record<string, { model: string; answer: string; option: string; token_count: number }> | undefined

    return {
      round: Number(payload.round ?? roundNumber),
      accuracy: Number((payload.acc as number | undefined) ?? 0),
      strategy: strategy?.active_strategy ?? "unknown",
      consensus: Number(strategy?.consensus_ratio ?? 0),
      tokens: tokens
        ? Object.values(tokens).reduce((sum, item) => sum + item.first + item.final, 0)
        : 0,
      gt: String(payload.gt ?? ""),
      pred: String(payload.pred ?? ""),
      question: String(payload.question ?? ""),
      firstRound,
      secondRound,
      graph: (payload.graph as Record<string, string>) ?? {},
      secondaryGraph: (payload.secondary_graph as Record<string, string>) ?? {},
      simMatrix: (payload.sim_matrix as number[][]) ?? [],
      twoRoundMetrics: (payload.two_round_metrics as Record<string, number>) ?? {},
    }
  }, [payload, roundNumber])

  return (
    <div className="mx-auto flex w-full max-w-[1680px] flex-col gap-8 px-4 py-8 md:px-6">
      <div className="flex items-center justify-between gap-4">
        <Link
          href={buildExperimentHref(experimentId)}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/85 px-4 py-2 text-sm font-medium text-slate-600 transition hover:border-slate-300 hover:text-slate-950"
        >
          <ArrowLeft className="size-4" />
          返回实验详情
        </Link>
        <Badge className="rounded-full bg-slate-950 px-4 py-1.5 text-xs uppercase tracking-[0.22em] text-white">
          第 {roundNumber} 轮
        </Badge>
      </div>

      <section className="rounded-[2rem] border border-white/70 bg-white/88 p-6 shadow-[0_30px_120px_-40px_rgba(15,23,42,0.35)] backdrop-blur-xl md:p-8">
        <div className="max-w-4xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-sky-700">
            <Sparkles className="size-3.5" />
            轮次检查
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950 md:text-5xl">第 {roundNumber} 轮深度查看</h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 md:text-base">
            本视图直接展示 exp.py 生成的原始 JSON：完整题目、第一轮与第二轮回答、通信图、相似度矩阵及各 Agent 的 Token 消耗。
          </p>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-4">
          <Metric label="准确率" value={formatPercent(roundMetrics?.accuracy ?? 0)} icon={Target} />
          <Metric label="Token" value={formatTokenCount(roundMetrics?.tokens ?? 0)} icon={Database} />
          <Metric label="策略" value={formatModeLabel(roundMetrics?.strategy ?? "unknown")} icon={Layers3} />
          <Metric label="共识率" value={formatPercent(roundMetrics?.consensus ?? 0)} icon={Timer} />
        </div>
      </section>

      {error ? (
        <Card className="border-rose-200 bg-rose-50/90 text-rose-900">
          <CardContent className="px-5 py-4 text-sm">{error}</CardContent>
        </Card>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <FileJson className="size-4" />
              轮次数据
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
              <div className="text-[11px] uppercase tracking-[0.24em] text-slate-400">题目</div>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-700">{roundMetrics?.question ?? ""}</p>
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              <InfoBox label="标准答案" value={roundMetrics?.gt ?? "-"} />
              <InfoBox label="预测答案" value={roundMetrics?.pred ?? "-"} />
              <InfoBox label="轮次" value={String(roundMetrics?.round ?? roundNumber)} />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <ListPanel title="第一轮回答" items={roundMetrics?.firstRound ?? {}} />
              <ListPanel title="第二轮回答" items={roundMetrics?.secondRound ?? {}} />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <GraphPanel title="主通信图" data={roundMetrics?.graph ?? {}} />
              <GraphPanel title="次级通信图" data={roundMetrics?.secondaryGraph ?? {}} />
            </div>

            <div className="rounded-3xl border border-slate-200 bg-slate-950 p-4 text-white">
              <div className="mb-3 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-slate-300">
                <Copy className="size-4" />
                原始 JSON
              </div>
              <ScrollArea className="h-[360px] rounded-2xl bg-slate-900 p-4">
                <pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-6 text-slate-200">
                  {loading ? "加载中..." : JSON.stringify(payload, null, 2)}
                </pre>
              </ScrollArea>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <GitBranch className="size-4" />
              相似度矩阵
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <ScrollArea className="h-[780px] pr-4">
              {loading ? (
                <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500">正在加载轮次数据...</div>
              ) : (
                <div className="space-y-4">
                  {(roundMetrics?.simMatrix ?? []).map((row, rowIndex) => (
                    <div key={rowIndex} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
                      <div className="mb-3 text-[11px] uppercase tracking-[0.24em] text-slate-400">智能体 {rowIndex + 1}</div>
                      <div className="grid grid-cols-4 gap-2 md:grid-cols-8">
                        {row.map((value, colIndex) => (
                          <div
                            key={colIndex}
                            className="rounded-xl border border-white bg-white px-2 py-3 text-center text-[11px] font-mono text-slate-700 shadow-sm"
                            style={{ backgroundColor: `rgba(14, 165, 233, ${Math.max(0.08, Math.min(0.8, value))})` }}
                          >
                            {value.toFixed(2)}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

function Metric({ label, value, icon: Icon }: { label: string; value: string; icon: any }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
      <div className="inline-flex size-10 items-center justify-center rounded-2xl bg-slate-950 text-white">
        <Icon className="size-4" />
      </div>
      <div className="mt-4 text-[11px] uppercase tracking-[0.24em] text-slate-400">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-950">{value}</div>
    </div>
  )
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
      <div className="text-[11px] uppercase tracking-[0.24em] text-slate-400">{label}</div>
      <div className="mt-2 text-lg font-semibold text-slate-950">{value}</div>
    </div>
  )
}

function ListPanel({ title, items }: { title: string; items: Record<string, any> }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
      <div className="mb-3 text-[11px] uppercase tracking-[0.24em] text-slate-400">{title}</div>
      <div className="space-y-2">
        {Object.entries(items).map(([agent, info]) => (
          <div key={agent} className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-slate-950">{agent}</div>
                <div className="text-xs text-slate-400">{info.model}</div>
              </div>
              <Badge className="rounded-full bg-slate-950 px-3 py-1 text-xs text-white">{info.option}</Badge>
            </div>
            <div className="mt-2 text-xs text-slate-500">Token: {info.token_count}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function GraphPanel({ title, data }: { title: string; data: Record<string, string> }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
      <div className="mb-3 text-[11px] uppercase tracking-[0.24em] text-slate-400">{title}</div>
      <div className="space-y-2">
        {Object.entries(data).length ? (
          Object.entries(data).map(([from, to]) => (
            <div key={`${from}-${to}`} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700">
              <span className="font-medium text-slate-950">{from}</span>
              <span className="text-slate-400">→</span>
              <span>{to}</span>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500">本轮没有次级通信图。</div>
        )}
      </div>
    </div>
  )
}