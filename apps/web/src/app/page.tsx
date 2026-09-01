import Link from "next/link";

const SCENARIOS = [
  {
    href: "/capacity-plan",
    title: "以渣定产 · 园区物料平衡仿真",
    description: "磷石膏消纳能力约束下，多支路负荷压减方案推演。",
    status: "已实现" as const,
  },
  {
    href: "/xifeng",
    title: "交椅山渣库 · 渗滤液早期预警（示意）",
    description: "先导指标能否比总磷泉点超标更早触发预警——合成示意数据演示。",
    status: "已实现" as const,
  },
];

export default function Home() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-16">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">序安 Process Sentinel</h1>
        <p className="text-sm text-foreground/70">
          只读采集数据，不接管 DCS 生产控制；所有输出仅作预测/预警/仿真建议，供工艺工程师、操作员参考。
        </p>
      </div>
      <div className="flex flex-col gap-3">
        {SCENARIOS.map((scenario) => (
          <Link
            key={scenario.href}
            href={scenario.href}
            className="flex flex-col gap-1 rounded-lg border border-foreground/10 p-4 transition hover:border-foreground/30"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">{scenario.title}</span>
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-800">
                {scenario.status}
              </span>
            </div>
            <span className="text-sm text-foreground/60">{scenario.description}</span>
          </Link>
        ))}
      </div>
    </main>
  );
}
