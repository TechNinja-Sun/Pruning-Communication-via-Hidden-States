"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { ActivitySquare, BarChart4, History, Radar } from "lucide-react"

import { cn } from "@/lib/utils"

const navItems = [
  { href: "/", label: "实时", icon: ActivitySquare },
  { href: "/history", label: "历史", icon: History },
  { href: "/compare", label: "对比", icon: BarChart4 },
  { href: "/history", label: "案例", icon: Radar },
]

export function SiteNav() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-50 border-b border-white/60 bg-white/78 backdrop-blur-xl supports-[backdrop-filter]:bg-white/72">
      <div className="mx-auto flex w-full max-w-[1680px] items-center justify-between gap-4 px-4 py-3 md:px-6">
        <Link href="/" className="group flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg shadow-slate-900/15 transition-transform duration-300 group-hover:scale-[1.02]">
            <ActivitySquare className="size-5" />
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">
              PruneComm-HS
            </div>
            <div className="text-sm font-semibold text-slate-950">
              实验洞察平台
            </div>
          </div>
        </Link>

        <nav className="flex flex-wrap items-center justify-end gap-2">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`)
            const Icon = item.icon

            return (
              <Link
                key={`${item.href}-${item.label}`}
                href={item.href}
                className={cn(
                  "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all",
                  active
                    ? "border-slate-950 bg-slate-950 text-white shadow-lg shadow-slate-900/10"
                    : "border-slate-200 bg-white/80 text-slate-600 hover:border-slate-300 hover:text-slate-950"
                )}
              >
                <Icon className="size-4" />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </div>
    </header>
  )
}