import Link from "next/link";

const SCENARIOS = [
  {
    href: "/capacity-plan",
    icon: "⚖️",
    title: "以渣定产 · 园区物料平衡仿真",
    description: "磷石膏消纳能力约束下，多支路负荷压减方案推演。",
    status: "已实现" as const,
  },
  {
    href: "/xifeng",
    icon: "🚨",
    title: "交椅山渣库 · 渗滤液早期预警（示意）",
    description: "先导指标能否比总磷泉点超标更早触发预警——合成示意数据演示。",
    status: "已实现" as const,
  },
  {
    href: "/flotation",
    icon: "🌀",
    title: "浮选投料 · 滞后化验软测量方法论验证",
    description: "真实铁矿浮选数据（CC0），验证实时传感器预测滞后化验指标的可行性。",
    status: "已实现" as const,
  },
  {
    href: "/metal-dosing",
    icon: "⚗️",
    title: "金属盐投加沉淀 · 磷酸铁沉淀方法论验证",
    description: "真实污水厂化学除磷SCADA数据（CC BY-NC 3.0），R²约0.68但需警惕闭环反馈耦合。",
    status: "已实现" as const,
  },
];

export default function Home() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-16">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-semibold text-accent-strong">序安 Process Sentinel</h1>
        <p className="text-sm text-foreground/70">
          只读采集数据，不接管 DCS 生产控制；所有输出仅作预测/预警/仿真建议，供工艺工程师、操作员参考。
        </p>
      </div>
      <div className="flex flex-col gap-3">
        {SCENARIOS.map((scenario) => (
          <Link
            key={scenario.href}
            href={scenario.href}
            className="flex items-center gap-4 rounded-xl border border-foreground/10 bg-surface p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-accent/40 hover:shadow-md"
          >
            <span className="text-3xl">{scenario.icon}</span>
            <div className="flex flex-1 flex-col gap-1">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium">{scenario.title}</span>
                <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-800">
                  {scenario.status}
                </span>
              </div>
              <span className="text-sm text-foreground/60">{scenario.description}</span>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
