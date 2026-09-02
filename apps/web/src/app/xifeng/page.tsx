"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ApiError,
  fetchLeachateScenario,
  type LeachateScenarioResponse,
} from "@/lib/api-client";
import { ProcessFlowDiagram, type FlowStage } from "@/components/process-flow-diagram";

const STAGE_VARIABLE_GROUPS: { stageId: string; icon: string; label: string; variableIds: string[] }[] = [
  { stageId: "pile", icon: "🏔️", label: "磷石膏堆场", variableIds: [] },
  {
    stageId: "membrane",
    icon: "🧱",
    label: "防渗膜 + 西侧边坡",
    variableIds: ["membrane_anomaly_score", "slope_displacement_mm"],
  },
  {
    stageId: "sump",
    icon: "🛢️",
    label: "库底导渗盲沟集水池",
    variableIds: ["conductivity_us_cm", "leachate_level_m", "ph"],
  },
  { stageId: "karst", icon: "🕳️", label: "岩溶通道运移", variableIds: [] },
  {
    stageId: "spring",
    icon: "💧",
    label: "桂花泉泉点出露",
    variableIds: ["total_phosphorus_mg_l"],
  },
];

function buildFlowStages(data: LeachateScenarioResponse): FlowStage[] {
  const { earlyWarning } = data;
  return STAGE_VARIABLE_GROUPS.map((group) => {
    if (group.variableIds.length === 0) {
      return {
        id: group.stageId,
        icon: group.icon,
        label: group.label,
        sublabel: "此环节报告显示无在线监测",
      };
    }
    const isWarningStage =
      earlyWarning.triggered && group.variableIds.includes(earlyWarning.warningVariableId ?? "");
    const isBreachStage = group.variableIds.includes(earlyWarning.breachVariableId);
    if (isBreachStage) {
      return {
        id: group.stageId,
        icon: group.icon,
        label: group.label,
        sublabel: "总磷浓度监测点",
        state: earlyWarning.triggered ? "alert" : "normal",
        badge: earlyWarning.triggered ? `第 ${earlyWarning.breachDay} 天超标` : undefined,
      };
    }
    return {
      id: group.stageId,
      icon: group.icon,
      label: group.label,
      sublabel: "先导指标监测点",
      state: isWarningStage ? "watch" : "normal",
      badge: isWarningStage ? `第 ${earlyWarning.warningDay} 天偏离` : undefined,
    };
  });
}

function VariableChart({
  title,
  unit,
  dayIndex,
  values,
  warningDay,
  breachDay,
  regulatoryLimit,
}: {
  title: string;
  unit: string;
  dayIndex: number[];
  values: number[];
  warningDay?: number | null;
  breachDay?: number | null;
  regulatoryLimit?: number;
}) {
  const data = dayIndex.map((day, i) => ({ day, value: values[i] }));

  return (
    <div className="flex h-56 flex-col rounded-lg border border-foreground/10 p-3">
      <h3 className="mb-1 text-sm font-medium">
        {title} <span className="text-foreground/40">({unit})</span>
      </h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 4, right: 12, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
          <XAxis dataKey="day" tick={{ fontSize: 10 }} label={{ value: "天", position: "insideBottomRight", fontSize: 10, offset: -2 }} />
          <YAxis tick={{ fontSize: 10 }} width={44} />
          <Tooltip labelFormatter={(day) => `第 ${day} 天`} />
          <Line type="monotone" dataKey="value" stroke="#2563eb" dot={false} strokeWidth={1.5} />
          {typeof warningDay === "number" && (
            <ReferenceLine x={warningDay} stroke="#d97706" strokeDasharray="4 2" label={{ value: "预警日", fontSize: 10, fill: "#d97706" }} />
          )}
          {typeof breachDay === "number" && (
            <ReferenceLine x={breachDay} stroke="#dc2626" strokeDasharray="4 2" label={{ value: "超标日", fontSize: 10, fill: "#dc2626" }} />
          )}
          {typeof regulatoryLimit === "number" && (
            <ReferenceLine y={regulatoryLimit} stroke="#dc2626" strokeDasharray="2 2" />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function XifengPage() {
  const [seed, setSeed] = useState(42);
  const [data, setData] = useState<LeachateScenarioResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- standard fetch-on-mount/seed-change pattern, no Suspense boundary set up for this demo page
    setLoading(true);
    setError(null);
    fetchLeachateScenario(seed)
      .then(setData)
      .catch((err) =>
        setError(
          err instanceof ApiError
            ? err.message
            : "场景数据加载失败，请检查后端服务是否已启动。",
        ),
      )
      .finally(() => setLoading(false));
  }, [seed]);

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">交椅山磷石膏渣库 · 渗滤液早期预警（示意）</h1>
        <p className="text-sm text-foreground/70">
          先导指标（防渗膜异常、电导率、边坡位移）理论上能在总磷于泉点超标之前反映异常——
          这个"先漏、后测到"的顺序是2017年环保督查真实发生过的事件，不是本demo编造的假设。
        </p>
        <div className="flex items-center gap-2 text-sm">
          <label htmlFor="seed">换一组模拟情景</label>
          <input
            id="seed"
            type="number"
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
            className="w-24 rounded border border-foreground/20 bg-transparent px-2 py-1"
          />
          <span className="text-foreground/50">改这个数字能看到不同的模拟结果，用来确认结论不是碰巧一次对的</span>
        </div>
      </header>

      {loading && <p className="text-sm text-foreground/50">加载中…</p>}
      {error && (
        <p className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {data && (
        <>
          <ProcessFlowDiagram
            title="渗漏路径推演：从堆场到泉点出露"
            stages={buildFlowStages(data)}
            leadTime={
              data.earlyWarning.triggered
                ? {
                    fromLabel: `⚠️ 先导指标异常（第 ${data.earlyWarning.warningDay} 天）`,
                    toLabel: `🚨 总磷超标（第 ${data.earlyWarning.breachDay} 天）`,
                    detail: `提前 ${data.earlyWarning.leadTimeDays} 天预警`,
                  }
                : undefined
            }
          />

          <div
            className={`rounded-lg border p-4 text-sm ${
              data.earlyWarning.triggered
                ? "border-amber-300 bg-amber-50 text-amber-900"
                : "border-foreground/10 bg-foreground/[0.03]"
            }`}
          >
            {data.earlyWarning.summary}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.variables.map((variable) => (
              <VariableChart
                key={variable.variableId}
                title={variable.variableName}
                unit={variable.unit}
                dayIndex={data.series.dayIndex}
                values={data.series.series[variable.variableId]}
                warningDay={
                  variable.leadingIndicator ? data.earlyWarning.warningDay : undefined
                }
                breachDay={
                  variable.variableId === data.earlyWarning.breachVariableId
                    ? data.earlyWarning.breachDay
                    : undefined
                }
                regulatoryLimit={
                  variable.variableId === "total_phosphorus_mg_l"
                    ? data.regulatoryLimitMgL
                    : undefined
                }
              />
            ))}
          </div>

          <section className="flex flex-col gap-2">
            <h2 className="text-sm font-medium">引用依据</h2>
            <ul className="flex flex-col gap-2 text-xs text-foreground/70">
              {data.citations.map((citation) => (
                <li key={citation.label} className="rounded border border-foreground/10 p-2">
                  <div className="font-medium text-foreground/90">{citation.label}</div>
                  <div>{citation.detail}</div>
                </li>
              ))}
            </ul>
          </section>

          <p className="rounded border border-foreground/10 bg-foreground/[0.03] px-3 py-2 text-xs text-foreground/60">
            数据来源披露：{data.disclosure}
          </p>
        </>
      )}
    </main>
  );
}
