"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import {
  ArrowRight,
  BadgeCheck,
  Brain,
  CircuitBoard,
  Database,
  LineChart as LineChartIcon,
  Search,
  Sparkles,
  Target,
  Timer,
  Users,
} from "lucide-react"
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  buildRoundHref,
  ExperimentDetail,
  formatModeLabel,
  formatPercent,
  formatTokenCount,
  getExperiment,
  searchRounds,
} from "@/lib/experiment-api"

const lineTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) {
    return null
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white/95 px-3 py-2 shadow-2xl backdrop-blur-sm">
      <div className="text-[10px] uppercase tracking-[0.24em] text-slate-400">第 {label} 轮</div>
      <div className="mt-1 text-sm font-semibold text-slate-950">{payload[0].name}</div>
      <div className="mt-2 text-xs text-slate-600">数值: {payload[0].value}</div>
    </div>
  )
}

export default function ExperimentDetailPage() {
  const params = useParams<{ experimentId: string }>()
  const experimentId = decodeURIComponent(params.experimentId)

  const [detail, setDetail] = useState<ExperimentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [matches, setMatches] = useState<{ round: number; question: string; acc: number; strategy: string }[]>([])

  useEffect(() => {
    let mounted = true

    const load = async () => {
      try {
        setLoading(true)
        const response = await getExperiment(experimentId)
        if (!mounted) {
          return
        }

        setDetail(response)
        setError(null)
      } catch (reason) {
        if (mounted) {
          setError(reason instanceof Error ? reason.message : "加载实验详情失败")
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
  }, [experimentId])

  useEffect(() => {
    if (!searchQuery.trim()) {
      setMatches([])
      return
    }

    let mounted = true
    const timer = window.setTimeout(async () => {
      try {
        const response = await searchRounds(experimentId, searchQuery.trim())
        if (!mounted) {
          return
        }

        setMatches(
          response.matches.map((item) => ({
            round: item.round,
            question: item.question,
            acc: item.acc,
            strategy: item.strategy,
          }))
        )
      } catch {
        if (mounted) {
          setMatches([])
        }
      }
    }, 250)

    return () => {
      mounted = false
      window.clearTimeout(timer)
    }
  }, [experimentId, searchQuery])

  const traceSeries = useMemo(() => {
    if (!detail?.trace?.length) {
      return []
    }

    return detail.trace.map((entry) => ({
      round: Number(entry.round ?? entry.idx ?? 0),
      accuracy: Number(((entry.acc as number | undefined) ?? 0) * 100),
      tokens: Number(entry.tokens ? Object.values(entry.tokens as Record<string, { first: number; final: number }>).reduce((sum, tokenInfo) => sum + tokenInfo.first + tokenInfo.final, 0) : 0),
      strategy: (entry.hybrid_strategy as Record<string, any> | undefined)?.active_strategy ?? "unknown",
      consensus: ((entry.hybrid_strategy as Record<string, any> | undefined)?.consensus_ratio ?? 0) * 100,
      question: typeof entry.question === "string" ? entry.question : "",
    }))
  }, [detail])

  const roundCards = useMemo(() => {
    if (!detail?.rounds?.length) {
      return []
    }

    return detail.rounds.filter((item) => {
      const lowered = searchQuery.trim().toLowerCase()
      if (!lowered) {
        return true
      }

      return item.question.toLowerCase().includes(lowered) || item.strategy.toLowerCase().includes(lowered)
    })
  }, [detail?.rounds, searchQuery])

  const topAgents = useMemo(() => {
    if (!detail?.trace?.length) {
      return []
    }

    const latest = detail.trace[detail.trace.length - 1]
    const answers = latest.second_round_answers as Record<string, { model: string; option: string; token_count: number }> | undefined
    if (!answers) {
      return []
    }

    return Object.entries(answers).map(([agent, info]) => ({ agent, model: info.model, option: info.option, token_count: info.token_count }))
  }, [detail])

  return (
    <div className="mx-auto flex w-full max-w-[1680px] flex-col gap-8 px-4 py-8 md:px-6">
      <section className="rounded-[2rem] border border-white/70 bg-white/88 p-6 shadow-[0_30px_120px_-40px_rgba(15,23,42,0.35)] backdrop-blur-xl md:p-8">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-3xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-sky-700">
              <Sparkles className="size-3.5" />
              实验详情
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-950 md:text-5xl">
              {experimentId}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 md:text-base">
              查看完整轨迹、逐轮汇总，并快速跳转到需要深入分析的案例。
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge className="rounded-full bg-slate-950 px-4 py-1.5 text-xs uppercase tracking-[0.22em] text-white">
              {formatModeLabel(detail?.mode ?? "loading")}
            </Badge>
            <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-4 py-1.5 text-xs uppercase tracking-[0.22em] text-slate-600">
              {detail?.round_count ?? 0} 轮
            </Badge>
            <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-4 py-1.5 text-xs uppercase tracking-[0.22em] text-slate-600">
              最终准确率 {formatPercent(detail?.final_accuracy ?? 0)}
            </Badge>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-4">
          <StatCard label="最终准确率" value={formatPercent(detail?.final_accuracy ?? 0)} icon={Target} />
          <StatCard label="总 Token" value={formatTokenCount(detail?.total_tokens ?? 0)} icon={Database} />
          <StatCard label="平均相似度" value={((detail?.average_similarity ?? 0) * 100).toFixed(1) + "%"} icon={Brain} />
          <StatCard label="总轮次" value={(detail?.round_count ?? 0).toString()} icon={Timer} />
        </div>
      </section>

      {error ? (
        <Card className="border-rose-200 bg-rose-50/90 text-rose-900">
          <CardContent className="px-5 py-4 text-sm">{error}</CardContent>
        </Card>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <LineChartIcon className="size-4" />
              轮次级信号
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
                <div className="mb-3 text-[11px] uppercase tracking-[0.24em] text-slate-400">准确率曲线</div>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={traceSeries}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <XAxis dataKey="round" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 100]} />
                      <Tooltip content={lineTooltip} />
                      <Area type="monotone" dataKey="accuracy" stroke="#0ea5e9" fill="#e0f2fe" strokeWidth={2.2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-slate-50/70 p-4">
                <div className="mb-3 text-[11px] uppercase tracking-[0.24em] text-slate-400">Token 曲线</div>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={traceSeries}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                      <XAxis dataKey="round" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip content={lineTooltip} />
                      <Line type="monotone" dataKey="tokens" stroke="#f97316" strokeWidth={2.2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <InfoPanel title="策略分布" icon={CircuitBoard}>
                <div className="space-y-3">
                  {Object.entries(detail?.strategy_distribution ?? {}).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3">
                      <span className="text-sm text-slate-600">{formatModeLabel(key)}</span>
                      <span className="font-mono text-sm font-semibold text-slate-950">{value}</span>
                    </div>
                  ))}
                </div>
              </InfoPanel>

              <InfoPanel title="最新 Agent 输出" icon={Users}>
                <div className="space-y-3">
                  {topAgents.map((item) => (
                    <div key={item.agent} className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-slate-950">{item.agent}</div>
                          <div className="text-xs text-slate-400">{item.model}</div>
                        </div>
                        <Badge className="rounded-full bg-slate-950 px-3 py-1 text-xs text-white">{item.option}</Badge>
                      </div>
                      <div className="mt-2 text-xs text-slate-500">Token 数: {item.token_count}</div>
                    </div>
                  ))}
                </div>
              </InfoPanel>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <Search className="size-4" />
              轮次检索
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <Search className="size-4 text-slate-400" />
              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="按题目内容或策略检索轮次"
                className="w-full bg-transparent text-sm text-slate-950 outline-none placeholder:text-slate-400"
              />
            </label>

            <ScrollArea className="mt-4 h-[620px] pr-4">
              <div className="space-y-3">
                {(searchQuery.trim() ? matches : roundCards).map((item) => (
                  <Link
                    key={item.round}
                    href={buildRoundHref(experimentId, item.round)}
                    className="group block rounded-2xl border border-slate-200 bg-slate-50/70 p-4 transition hover:-translate-y-0.5 hover:border-sky-200 hover:bg-white hover:shadow-lg"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge className="rounded-full bg-slate-950 px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-white">
                            第 {item.round} 轮
                          </Badge>
                          <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-slate-600">
                            {formatModeLabel(item.strategy)}
                          </Badge>
                        </div>
                        <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-700">{item.question}</p>
                      </div>
                      <ArrowRight className="mt-1 size-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-sky-500" />
                    </div>

                    <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
                      <MiniStat label="准确率" value={formatPercent(item.acc)} />
                      <MiniStat label="标准答案" value={item.gt || "-"} />
                      <MiniStat label="预测答案" value={item.pred || "-"} />
                    </div>
                  </Link>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

function StatCard({ label, value, icon: Icon }: { label: string; value: string; icon: any }) {
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

function InfoPanel({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white/80 p-4">
      <div className="mb-4 flex items-center gap-2 text-[11px] uppercase tracking-[0.24em] text-slate-400">
        <Icon className="size-4" />
        {title}
      </div>
      {children}
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.24em] text-slate-400">{label}</div>
      <div className="mt-1 font-mono text-sm font-semibold text-slate-950">{value}</div>
    </div>
  )
}