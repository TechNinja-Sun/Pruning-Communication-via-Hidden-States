"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import {
  ArrowRight,
  BarChart3,
  Database,
  Layers3,
  Medal,
  Sparkles,
  TrendingUp,
} from "lucide-react"
import {
  Bar,
  Line,
  ComposedChart,
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
  listExperiments,
} from "@/lib/experiment-api"

export default function ComparePage() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    const load = async () => {
      try {
        setLoading(true)
        const response = await listExperiments()
        if (mounted) {
          setExperiments(response.items)
          setError(null)
        }
      } catch (reason) {
        if (mounted) {
          setError(reason instanceof Error ? reason.message : "加载对比数据失败")
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
  }, [])

  const summaryByMode = useMemo(() => {
    return experiments.reduce<Record<string, { count: number; accuracy: number; tokens: number }>>((accumulator, item) => {
      const entry = accumulator[item.mode] ?? { count: 0, accuracy: 0, tokens: 0 }
      entry.count += 1
      entry.accuracy += item.final_accuracy
      entry.tokens += item.total_tokens
      accumulator[item.mode] = entry
      return accumulator
    }, {})
  }, [experiments])

  const modeData = useMemo(() => {
    return Object.entries(summaryByMode).map(([mode, entry]) => ({
      mode,
      count: entry.count,
      avg_accuracy: Number((entry.accuracy / entry.count).toFixed(3)) * 100,
      avg_tokens: Number((entry.tokens / entry.count / 1000).toFixed(1)),
    }))
  }, [summaryByMode])

  const leaderboard = useMemo(() => {
    return [...experiments].sort((left, right) => {
      const scoreLeft = left.final_accuracy / Math.max(left.total_tokens, 1)
      const scoreRight = right.final_accuracy / Math.max(right.total_tokens, 1)
      return scoreRight - scoreLeft
    })
  }, [experiments])

  const metrics = useMemo(() => {
    const count = experiments.length
    const averageAccuracy = count === 0 ? 0 : experiments.reduce((sum, item) => sum + item.final_accuracy, 0) / count
    const averageTokens = count === 0 ? 0 : experiments.reduce((sum, item) => sum + item.total_tokens, 0) / count

    return { count, averageAccuracy, averageTokens }
  }, [experiments])

  return (
    <div className="mx-auto flex w-full max-w-[1680px] flex-col gap-8 px-4 py-8 md:px-6">
      <section className="rounded-[2rem] border border-white/70 bg-white/88 p-6 shadow-[0_30px_120px_-40px_rgba(15,23,42,0.35)] backdrop-blur-xl md:p-8">
        <div className="max-w-4xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-sky-700">
            <Sparkles className="size-3.5" />
            策略对比
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-950 md:text-5xl">
            对比历史实验中的通信策略表现。
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 md:text-base">
            本页按策略模式聚合历史实验，并以单位 Token 的准确率效率进行排序，让高效实验优先展示。
          </p>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <Metric label="实验数" value={metrics.count.toString()} icon={Layers3} />
          <Metric label="平均准确率" value={formatPercent(metrics.averageAccuracy)} icon={TrendingUp} />
          <Metric label="平均 Token" value={formatTokenCount(metrics.averageTokens)} icon={Database} />
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
              <BarChart3 className="size-4" />
              策略汇总
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-[360px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={modeData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="mode" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="left" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fill: "#475569", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip />
                  <Bar yAxisId="left" dataKey="avg_accuracy" name="平均准确率 (%)" fill="#0ea5e9" radius={[10, 10, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="avg_tokens" name="平均 Token (k)" stroke="#f97316" strokeWidth={2.4} dot={{ r: 4 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="border-white/70 bg-white/88 shadow-[0_18px_70px_-30px_rgba(15,23,42,0.25)] backdrop-blur-xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <CardTitle className="flex items-center gap-2 text-sm uppercase tracking-[0.24em] text-slate-500">
              <Medal className="size-4" />
              效率排行榜
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <ScrollArea className="h-[420px] pr-4">
              <div className="space-y-3">
                {loading ? (
                  <div className="rounded-2xl border border-dashed border-slate-200 px-4 py-10 text-center text-sm text-slate-500">正在加载对比数据...</div>
                ) : (
                  leaderboard.slice(0, 12).map((item, index) => (
                    <Link
                      key={item.experiment_id}
                      href={buildExperimentHref(item.experiment_id)}
                      className="group block rounded-2xl border border-slate-200 bg-slate-50/70 p-4 transition hover:-translate-y-0.5 hover:border-sky-200 hover:bg-white hover:shadow-lg"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge className="rounded-full bg-slate-950 px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-white">
                              #{index + 1}
                            </Badge>
                            <Badge variant="outline" className="rounded-full border-slate-200 bg-white px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-slate-600">
                              {formatModeLabel(item.mode)}
                            </Badge>
                          </div>
                          <div className="mt-3 text-sm font-semibold text-slate-950">{item.experiment_id}</div>
                          <div className="mt-1 text-xs text-slate-400">{item.question_preview || "暂无题目预览"}</div>
                        </div>
                        <ArrowRight className="mt-1 size-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-sky-500" />
                      </div>

                      <div className="mt-4 grid grid-cols-3 gap-3 text-xs">
                        <MiniStat label="准确率" value={formatPercent(item.final_accuracy)} />
                        <MiniStat label="Token" value={formatTokenCount(item.total_tokens)} />
                        <MiniStat label="轮次数" value={item.round_count.toString()} />
                      </div>
                    </Link>
                  ))
                )}
              </div>
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

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.24em] text-slate-400">{label}</div>
      <div className="mt-1 font-mono text-sm font-semibold text-slate-950">{value}</div>
    </div>
  )
}