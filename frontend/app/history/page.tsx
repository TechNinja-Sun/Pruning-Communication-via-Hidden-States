"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import {
  ArrowRight,
  BarChart3,
  CalendarDays,
  Database,
  Filter,
  Flame,
  Layers3,
  RefreshCw,
  Search,
  Sparkles,
  TrendingUp,
} from "lucide-react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  buildExperimentHref,
  ExperimentSummary,
  formatModeLabel,
  formatPercent,
  formatTokenCount,
  getHealth,
  listExperiments,
} from "@/lib/experiment-api"

type SortKey = "recent" | "accuracy" | "tokens"

type ComparisonChartItem = {
  name: string
  accuracy: number
  tokens: number
  mode: string
}

const chartTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) {
    return null
  }

  const item = payload[0].payload as ComparisonChartItem
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/95 px-3 py-2 shadow-2xl backdrop-blur-sm">
      <div className="text-[10px] uppercase tracking-[0.24em] text-slate-400">{item.name}</div>
      <div className="mt-1 text-sm font-semibold text-slate-950">{formatModeLabel(item.mode)}</div>
      <div className="mt-2 text-xs text-slate-600">
        最终准确率: <span className="font-semibold text-slate-950">{item.accuracy.toFixed(1)}%</span>
      </div>
      <div className="text-xs text-slate-600">
        总 Token: <span className="font-semibold text-slate-950">{item.tokens.toFixed(1)}k</span>
      </div>
    </div>
  )
}

export default function HistoryPage() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState("")
  const [mode, setMode] = useState("all")
  const [sortKey, setSortKey] = useState<SortKey>("recent")
  const [health, setHealth] = useState<string>("检查中")

  const load = async (nextRefreshing = false) => {
    try {
      if (nextRefreshing) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      const [history, status] = await Promise.all([listExperiments(), getHealth().catch(() => null)])
      setExperiments(history.items)
      setHealth(status?.status ?? "离线")
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "加载实验历史失败")
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const filteredExperiments = useMemo(() => {
    const lowered = query.trim().toLowerCase()

    const items = experiments.filter((item) => {
      const matchesMode = mode === "all" || item.mode === mode
      const matchesQuery =
        !lowered ||
        item.experiment_id.toLowerCase().includes(lowered) ||
        item.question_preview.toLowerCase().includes(lowered) ||
        item.search_blob.toLowerCase().includes(lowered)

      return matchesMode && matchesQuery
    })

    return [...items].sort((left, right) => {
      if (sortKey === "accuracy") {
        return right.final_accuracy - left.final_accuracy
      }

      if (sortKey === "tokens") {
        return right.total_tokens - left.total_tokens
      }

      return right.experiment_id.localeCompare(left.experiment_id)
    })
  }, [experiments, mode, query, sortKey])

  const stats = useMemo(() => {
    const total = filteredExperiments.length
    const averageAccuracy =
      total === 0 ? 0 : filteredExperiments.reduce((sum, item) => sum + item.final_accuracy, 0) / total
    const totalTokens = filteredExperiments.reduce((sum, item) => sum + item.total_tokens, 0)
    const bestAccuracy = filteredExperiments[0]?.final_accuracy ?? 0
    const strategyTally = filteredExperiments.reduce<Record<string, number>>((accumulator, item) => {
      accumulator[item.mode] = (accumulator[item.mode] ?? 0) + 1
      return accumulator
    }, {})

    return { total, averageAccuracy, totalTokens, bestAccuracy, strategyTally }
  }, [filteredExperiments])

  const comparisonData = filteredExperiments.slice(0, 12).map((item) => ({
    name: item.experiment_id.replace(/^result_/, "").slice(0, 12),
    accuracy: Number((item.final_accuracy * 100).toFixed(1)),
    tokens: Number((item.total_tokens / 1000).toFixed(1)),
    mode: item.mode,
  }))

  return (
    <div className="mx-auto flex w-full max-w-[1680px] flex-col gap-8 px-4 py-8 md:px-6">
      <section className="overflow-hidden rounded-[2rem] border border-white/70 bg-white/85 p-6 shadow-[0_30px_120px_-40px_rgba(15,23,42,0.35)] backdrop-blur-xl md:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-sky-700">
              <Sparkles className="size-3.5" />
              历史实验浏览
            </div>
            <h1 className="text-4xl font-semibold tracking-tight text-slate-950 md:text-6xl">
              浏览实验、对比策略、直达任意轮次。
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-600 md:text-base">
              本页会扫描 exp 目录下所有 JSON 实验结果，并提供可检索的分析视图。你可以按策略筛选、查看每一轮结果，并继续下钻到单个案例。
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 lg:w-[420px] lg:grid-cols-1 xl:grid-cols-3">
            <Metric label="实验数" value={stats.total.toString()} icon={Database} tone="sky" />
            <Metric label="平均准确率" value={formatPercent(stats.averageAccuracy)} icon={TrendingUp} tone="emerald" />
            <Metric label="服务状态" value={health} icon={Flame} tone="amber" />
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.45fr_0.95fr_0.75fr]">
        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <Search className="size-4" />
              历史检索
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 pt-4">
            <div className="grid gap-3 md:grid-cols-[1.2fr_0.6fr_0.6fr]">
              <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                <Search className="size-4 text-slate-400" />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="输入实验 ID、题目内容或模型备注"
                  className="w-full bg-transparent text-sm text-slate-950 outline-none placeholder:text-slate-400"
                />
              </label>

              <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                <Filter className="size-4 text-slate-400" />
                <select value={mode} onChange={(event) => setMode(event.target.value)} className="w-full bg-transparent outline-none">
                  <option value="all">全部策略</option>
                  <option value="dissimilar">低相似</option>
                  <option value="similar">高相似</option>
                  <option value="random">随机</option>
                  <option value="mixed">混合</option>
                  <option value="dissimilar_then_similar">先低相似后高相似</option>
                  <option value="hybrid">混合策略</option>
                </select>
              </label>

              <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                <Layers3 className="size-4 text-slate-400" />
                <select value={sortKey} onChange={(event) => setSortKey(event.target.value as SortKey)} className="w-full bg-transparent outline-none">
                  <option value="recent">最新优先</option>
                  <option value="accuracy">准确率优先</option>
                  <option value="tokens">Token 消耗优先</option>
                </select>
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
              {Object.entries(stats.strategyTally).map(([key, count]) => (
                <Badge key={key} variant="outline" className="rounded-full border-slate-200 bg-white px-3 py-1 text-slate-600">
                  {formatModeLabel(key)} · {count}
                </Badge>
              ))}
              <button
                type="button"
                onClick={() => void load(true)}
                className="ml-auto inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:text-slate-950"
              >
                <RefreshCw className={`size-3.5 ${refreshing ? "animate-spin" : ""}`} />
                刷新索引
              </button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <CalendarDays className="size-4" />
              策略分布
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={Object.entries(stats.strategyTally).map(([key, value]) => ({ key, value }))}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="key" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#0ea5e9" radius={[10, 10, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <BarChart3 className="size-4" />
              快速概览
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 pt-4">
            <div className="rounded-2xl bg-slate-950 px-4 py-3 text-white">
              <div className="text-[11px] uppercase tracking-[0.24em] text-slate-300">最高准确率</div>
              <div className="mt-2 text-2xl font-semibold">{formatPercent(stats.bestAccuracy)}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div className="text-[11px] uppercase tracking-[0.24em] text-slate-400">Token 总量</div>
              <div className="mt-2 text-2xl font-semibold text-slate-950">{formatTokenCount(stats.totalTokens)}</div>
            </div>
          </CardContent>
        </Card>
      </section>

      {error ? (
        <Card className="border-rose-200 bg-rose-50/90 text-rose-900">
          <CardContent className="px-5 py-4 text-sm">{error}</CardContent>
        </Card>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <TrendingUp className="size-4" />
              准确率与 Token 成本
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-[360px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData} margin={{ left: 4, right: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="left" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={chartTooltip} />
                  <Bar yAxisId="left" dataKey="accuracy" name="准确率 (%)" fill="#0ea5e9" radius={[10, 10, 0, 0]} />
                  <Bar yAxisId="right" dataKey="tokens" name="Token (k)" fill="#f97316" radius={[10, 10, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <Layers3 className="size-4" />
              实验列表
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            {loading ? (
              <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500">
                正在加载历史索引...
              </div>
            ) : (
              <ScrollArea className="h-[460px] pr-4">
                <div className="space-y-3">
                  {filteredExperiments.map((item) => (
                    <Link
                      key={item.experiment_id}
                      href={buildExperimentHref(item.experiment_id)}
                      className="group block rounded-2xl border border-slate-200 bg-slate-50/70 p-4 transition hover:-translate-y-0.5 hover:border-sky-200 hover:bg-white hover:shadow-lg"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge className="rounded-full bg-slate-950 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-white">
                              {formatModeLabel(item.mode)}
                            </Badge>
                            <span className="text-xs text-slate-400">{item.experiment_id}</span>
                          </div>
                          <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-700">
                            {item.question_preview || "暂无题目预览"}
                          </p>
                        </div>
                        <ArrowRight className="mt-1 size-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-sky-500" />
                      </div>

                      <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
                        <MiniStat label="准确率" value={formatPercent(item.final_accuracy)} />
                        <MiniStat label="轮次数" value={item.round_count.toString()} />
                        <MiniStat label="Token" value={formatTokenCount(item.total_tokens)} />
                      </div>
                    </Link>
                  ))}
                  {!filteredExperiments.length ? (
                    <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500">
                      当前筛选条件下没有匹配的实验。
                    </div>
                  ) : null}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  )
}

function Metric({ label, value, icon: Icon, tone }: { label: string; value: string; icon: any; tone: "sky" | "emerald" | "amber" }) {
  const toneMap = {
    sky: "from-sky-500 to-cyan-500",
    emerald: "from-emerald-500 to-teal-500",
    amber: "from-amber-500 to-orange-500",
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-slate-50/80 p-4 shadow-sm">
      <div className={`inline-flex size-10 items-center justify-center rounded-2xl bg-gradient-to-br ${toneMap[tone]} text-white`}>
        <Icon className="size-4" />
      </div>
      <div className="mt-4 text-[11px] uppercase tracking-[0.24em] text-slate-400">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-slate-950">{value}</div>
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