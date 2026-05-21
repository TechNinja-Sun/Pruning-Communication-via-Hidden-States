"use client"
import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge" 
import { 
  Target, Zap, Settings2, Link2, 
  Timer, Coins, Cpu, Terminal, Download, TrendingUp, Activity, BarChart3
} from "lucide-react"
import { 
  LineChart, Line, CartesianGrid, Tooltip, 
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  ScatterChart, Scatter, ZAxis
} from 'recharts';
import { motion } from 'framer-motion';
import { domToPng } from 'modern-screenshot';

// --- 科研风格公用配置 ---
const axisConfig = {
  stroke: "#475569", 
  tick: { fill: "#1e293b", fontSize: 10, fontFamily: 'ui-monospace, monospace' }, 
  tickLine: { stroke: "#cbd5e1" },
};

const ScientificTooltip = ({ active, payload, label, unit }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/95 p-2 border border-slate-200 shadow-xl rounded backdrop-blur-sm text-[10px]">
        <p className="font-bold text-slate-900 border-b border-slate-100 pb-1 mb-1">{`第 ${label} 轮`}</p>
        <p className="text-sky-700">
          {`${payload[0].name}: `}
          <span className="font-mono font-bold text-slate-950">{payload[0].value.toLocaleString()}</span>
          {` ${unit}`}
        </p>
      </div>
    );
  }
  return null;
};

export default function AgentDashboard() {
  const [messages, setMessages] = useState<any[]>([])
  const [accuracy, setAccuracy] = useState(0)
  const [isConnected, setIsConnected] = useState(false)
  const [agentCount, setAgentCount] = useState(3)
  const [matrix, setMatrix] = useState<number[][]>([])
  const [tokenHistory, setTokenHistory] = useState<any[]>([])
  const [timeHistory, setTimeHistory] = useState<any[]>([])
  const [accHistory, setAccHistory] = useState<any[]>([])
  const [connections, setConnections] = useState<Record<string, string>>({})
  const [progress, setProgress] = useState({ current: 0, total: 1, startTime: 0 })

  const socketRef = useRef<WebSocket | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  
  // 引用 6 个卡片的 Ref 数组
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // --- 核心修复：重命名后的保存函数 ---
  const saveAsImage = useCallback(async () => {
    const cardNames = ['进度', '日志', '映射', '准确率', 'Token', '相似度'];
    const timestamp = new Date().getTime();

    for (let i = 0; i < cardRefs.current.length; i++) {
      const cardDom = cardRefs.current[i];
      if (!cardDom) continue;
      try {
        const dataUrl = await domToPng(cardDom, {
          backgroundColor: '#ffffff',
          scale: 3, 
          quality: 1
        });
        const link = document.createElement('a');
        link.download = `Fig${i+1}_${cardNames[i]}_${timestamp}.png`;
        link.href = dataUrl;
        link.click();
        await new Promise(r => setTimeout(r, 200)); 
      } catch (err) {
        console.error(err);
      }
    }
  }, []);

  const flatSimilarityData = React.useMemo(() => {
    if (!matrix.length) return [];
    const names = Array.from({ length: agentCount }, (_, i) => `A${i+1}`);
    const data: any[] = [];
    matrix.forEach((row, x) => {
      row.forEach((val, y) => {
        data.push({ x: names[x], y: names[y], val, size: val * 100 });
      });
    });
    return data;
  }, [matrix, agentCount]);

  const startExperiment = () => {
    if (socketRef.current) socketRef.current.close()
    socketRef.current = new WebSocket('ws://localhost:8000/ws')
    socketRef.current.onopen = () => {
      setIsConnected(true)
      setMessages([]); setMatrix([]); setTokenHistory([]); setTimeHistory([]); setAccHistory([]); setConnections({});
      setProgress({ current: 0, total: 1, startTime: Date.now() });
      socketRef.current?.send(JSON.stringify({ nums_agents: agentCount }))
    }
    socketRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'task_config') setProgress(prev => ({ ...prev, total: data.total }));
      else if (data.type === 'agent_think') setMessages(prev => [...prev, { ...data, id: Date.now() + Math.random() }])
      else if (data.type === 'step_analytics') {
        const stepIdx = data.idx + 1;
        setAccuracy(data.accuracy); setMatrix(data.matrix); setConnections(data.connections);
        setProgress(prev => ({ ...prev, current: stepIdx }));
        setAccHistory(prev => [...prev, { round: stepIdx, acc: data.accuracy * 100 }].slice(-100))
        setTimeHistory(prev => [...prev, { round: stepIdx, time: data.duration }].slice(-100))
        const totalTokens = Object.values(data.token_usage as Record<string, any>).reduce((sum, curr) => sum + curr.first + curr.final, 0)
        setTokenHistory(prev => [...prev, { round: stepIdx, tokens: totalTokens }].slice(-100))
      }
    }
    socketRef.current.onclose = () => setIsConnected(false)
  }

  return (
    <div className="min-h-screen bg-white text-slate-950 p-6 font-sans">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 border-b border-slate-100 pb-6">
        <div>
          <h1 className="text-2xl font-black tracking-tighter text-slate-900 uppercase">
            PruneComm <span className="text-sky-600">实验看板</span>
          </h1>
          <p className="text-slate-400 text-[9px] font-mono tracking-widest mt-1">面向科研实验的实时数据终端</p>
        </div>

        <div className="flex items-center gap-4">
          <button onClick={saveAsImage} className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded text-[10px] font-bold uppercase hover:bg-slate-800 transition-all">
            <Download size={14} /> 导出图表 (PNG)
          </button>
          
          <div className="flex items-center gap-3 bg-slate-50 px-4 py-2 rounded border border-slate-200">
            <Settings2 size={14} className="text-slate-400" />
            <input type="range" min="2" max="8" value={agentCount} disabled={isConnected}
              onChange={(e) => setAgentCount(parseInt(e.target.value))} className="w-24 accent-sky-600 cursor-pointer" />
            <span className="text-sky-700 font-mono font-bold text-xs">{agentCount}</span>
          </div>
          
          <button onClick={startExperiment} disabled={isConnected}
            className={`px-8 py-2 rounded font-bold text-[10px] uppercase tracking-widest transition-all ${
              isConnected ? 'bg-slate-100 text-slate-400' : 'bg-sky-600 text-white hover:bg-sky-700'
            }`}>
            {isConnected ? '执行中...' : '开始实验'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard title="准确率" value={`${(accuracy * 100).toFixed(1)}%`} color="text-emerald-600" />
        <StatCard title="时延" value={timeHistory.length > 0 ? `${timeHistory[timeHistory.length-1].time}s` : "0.0s"} color="text-sky-600" />
        <StatCard title="Token" value={tokenHistory.reduce((a, b) => a + b.tokens, 0).toLocaleString()} color="text-amber-600" />
        <StatCard title="智能体数" value={agentCount.toString()} color="text-indigo-600" />
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-8 space-y-6">
          {/* Fig 1: Progress */}
          <Card ref={el => cardRefs.current[0] = el} className="bg-white border-slate-200 shadow-sm">
            <div className="px-4 py-3 bg-slate-50/50 border-b border-slate-100 flex justify-between items-center">
              <span className="text-[10px] font-bold text-slate-800 uppercase italic">Fig 1. Task Progress Control</span>
              <span className="font-mono text-[9px] text-slate-500 uppercase tracking-tighter">
                速度: {metrics(progress, isConnected).speed} | 预计剩余: {metrics(progress, isConnected).eta}
              </span>
            </div>
            <CardContent className="p-5">
              <div className="flex items-center gap-6">
                <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <motion.div className="h-full bg-sky-600" initial={{ width: 0 }} animate={{ width: `${(progress.current/progress.total)*100}%` }} />
                </div>
                <div className="font-mono text-xs font-bold text-slate-900">
                  {Math.round((progress.current/progress.total)*100)}%
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Fig 2: Logs */}
          <Card ref={el => cardRefs.current[1] = el} className="bg-white border-slate-200 shadow-sm h-[400px] flex flex-col">
            <CardHeader className="py-3 px-4 bg-slate-50/50 border-b border-slate-100">
              <CardTitle className="text-[10px] font-bold text-slate-800 uppercase">图2：智能体推理流</CardTitle>
            </CardHeader>
            <ScrollArea className="flex-1 p-4 font-mono">
              {messages.map((msg, i) => (
                <div key={i} className="mb-4 pb-3 border-b border-slate-50">
                  <div className="flex items-center gap-2 mb-1 text-[10px]">
                    <span className="font-bold text-sky-600">{msg.agent}</span>
                    <span className="text-slate-300">|</span>
                    <span className="text-slate-400 uppercase tracking-tighter">第 {msg.round} 轮</span>
                  </div>
                  <p className="text-[11px] text-slate-700 leading-relaxed">{msg.content}</p>
                </div>
              ))}
              <div ref={scrollRef} />
            </ScrollArea>
          </Card>
        </div>

        <div className="col-span-4 space-y-6">
          {/* Fig 3: Mapping */}
          <Card ref={el => cardRefs.current[2] = el} className="bg-white border-slate-200 shadow-sm h-40">
            <CardHeader className="py-2.5 px-4 bg-slate-50/50 border-b border-slate-100 text-[10px] font-bold uppercase">图3：交互映射</CardHeader>
            <CardContent className="flex justify-around items-center h-24 pt-4">
              {Array.from({ length: agentCount }).map((_, i) => (
                <div key={i} className="flex flex-col items-center">
                  <div className={`w-8 h-8 rounded border flex items-center justify-center text-[9px] font-bold ${connections[`Agent_${i+1}`] ? 'bg-sky-50 border-sky-200 text-sky-700' : 'bg-slate-50 border-slate-100 text-slate-400'}`}>A{i+1}</div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Fig 4: Accuracy Curve */}
          <Card ref={el => cardRefs.current[3] = el} className="bg-white border-slate-200 shadow-sm h-52">
            <CardHeader className="py-2.5 px-4 bg-slate-50/50 border-b border-slate-100 text-[10px] font-bold uppercase">图4：收敛曲线</CardHeader>
            <CardContent className="h-32 pt-4 pr-4 pl-0">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={accHistory} margin={{ left: -20, bottom: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="round" {...axisConfig} />
                  <YAxis {...axisConfig} domain={[0, 100]} />
                  <Tooltip content={<ScientificTooltip unit="% 准确率" />} />
                  <Area type="monotone" dataKey="acc" stroke="#10b981" fill="#ecfdf5" strokeWidth={1.5} />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Fig 5: Tokens */}
          <Card ref={el => cardRefs.current[4] = el} className="bg-white border-slate-200 shadow-sm h-52">
            <CardHeader className="py-2.5 px-4 bg-slate-50/50 border-b border-slate-100 text-[10px] font-bold uppercase">图5：资源消耗</CardHeader>
            <CardContent className="h-32 pt-4 pr-4 pl-0">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={tokenHistory} margin={{ left: -10, bottom: -10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="round" {...axisConfig} />
                  <YAxis {...axisConfig} />
                  <Tooltip content={<ScientificTooltip unit="token" />} />
                  <Line type="stepAfter" dataKey="tokens" stroke="#3b82f6" strokeWidth={1.5} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Fig 6: Similarity Heatmap */}
          <Card ref={el => cardRefs.current[5] = el} className="bg-white border-slate-200 shadow-sm h-60">
            <CardHeader className="py-2.5 px-4 bg-slate-50/50 border-b border-slate-100 text-[10px] font-bold uppercase">图6：相似度热图</CardHeader>
            <CardContent className="h-44 pt-4 pr-4 pl-2">
              {matrix.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ bottom: 0, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} horizontal={false} />
                    {/* 指定 dataKey 为 'x'，类型为类目 */}
                    <XAxis type="category" dataKey="x" name="智能体 X" {...axisConfig} tickLine={false} />
                    {/* 指定 dataKey 为 'y'，类型为类目 */}
                    <YAxis type="category" dataKey="y" name="智能体 Y" {...axisConfig} width={30} tickLine={false} />
                    <ZAxis type="number" dataKey="size" range={[0, 500]} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <Scatter 
                      name="相似度"
                      data={flatSimilarityData} 
                      shape={(props: any) => {
                        const { cx, cy, payload } = props;
                        // --- 核心修复：防御性检查，防止 NaN 崩溃 ---
                        if (isNaN(cx) || isNaN(cy) || cx === null || cy === null) return null;
                        
                        // 动态计算方块大小，确保它居中
                        const size = 20; 
                        return (
                          <rect 
                            x={cx - size / 2} 
                            y={cy - size / 2} 
                            width={size} 
                            height={size} 
                            fill={`rgba(2, 132, 199, ${payload.val})`} 
                            stroke="#fff" 
                            strokeWidth={1} 
                          />
                        );
                      }} 
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-[10px] font-mono text-slate-400 italic">
                  等待相似度矩阵数据...
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function StatCard({ title, value, color }: any) {
  return (
    <div className="bg-white border border-slate-100 p-4 rounded shadow-sm">
      <p className="text-[9px] text-slate-400 font-bold uppercase mb-1">{title}</p>
      <p className={`text-xl font-mono font-black ${color}`}>{value}</p>
    </div>
  )
}

function metrics(p: any, is: boolean) {
  if (!is || p.current === 0) return { speed: "0.0 轮/s", eta: "00:00" };
  const sec = (Date.now() - p.startTime) / 1000;
  const speed = p.current / sec;
  const eta = Math.round((p.total - p.current) / speed);
  return { speed: `${speed.toFixed(1)} 轮/s`, eta: `${Math.floor(eta/60)}:${(eta%60).toString().padStart(2,'0')}` };
}
