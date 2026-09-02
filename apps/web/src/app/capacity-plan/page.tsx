"use client";

import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ApiError,
  simulateCapacityPlan,
  type CapacityPlanResponse,
  type ProductionLineInput,
} from "@/lib/api-client";

const STRATEGY_COLORS: Record<string, string> = {
  proportional: "#2563eb",
  priority_first: "#d97706",
  equal_share: "#059669",
};

function CapacityGauge({
  requestedLowTpd,
  requestedHighTpd,
  capTpd,
  withinCap,
}: {
  requestedLowTpd: number;
  requestedHighTpd: number;
  capTpd: number;
  withinCap: boolean;
}) {
  const scaleMax = Math.max(capTpd, requestedHighTpd) * 1.15;
  const capPct = (capTpd / scaleMax) * 100;
  const lowPct = (requestedLowTpd / scaleMax) * 100;
  const highPct = (requestedHighTpd / scaleMax) * 100;
  const fillColor = withinCap ? "bg-emerald-500" : "bg-red-500";

  return (
    <div className="flex flex-col gap-2 rounded-xl border border-foreground/10 bg-surface/60 p-4">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium">磷石膏产出量 vs 消纳能力上限</span>
        <span className={withinCap ? "text-emerald-700" : "text-red-600"}>
          {withinCap ? "在上限内" : "超出上限"}
        </span>
      </div>
      <div className="relative h-8 w-full overflow-hidden rounded-full bg-foreground/10">
        <div
          className={`absolute inset-y-0 left-0 rounded-full ${fillColor} opacity-90`}
          style={{ width: `${Math.min(highPct, 100)}%` }}
        />
        <div
          className={`absolute inset-y-0 left-0 rounded-full ${fillColor}`}
          style={{ width: `${Math.min(lowPct, 100)}%` }}
        />
        <div
          className="absolute inset-y-0 w-0.5 bg-foreground/70"
          style={{ left: `${Math.min(capPct, 100)}%` }}
        />
        <span
          className="absolute -top-5 -translate-x-1/2 text-[11px] font-medium text-foreground/70"
          style={{ left: `${Math.min(capPct, 100)}%` }}
        >
          上限 {capTpd}
        </span>
      </div>
      <div className="flex justify-between text-xs text-foreground/50">
        <span>0</span>
        <span>
          预计产出 {requestedLowTpd}–{requestedHighTpd} 吨/天
        </span>
        <span>{Math.round(scaleMax)}</span>
      </div>
    </div>
  );
}

function defaultLines(): ProductionLineInput[] {
  return [
    { id: "map_dap", name: "磷肥支路（MAP/DAP）", requestedP2o5Tpd: 300, priority: 3 },
    { id: "ppa", name: "净化磷酸支路（PPA→磷酸铁）", requestedP2o5Tpd: 150, priority: 5 },
  ];
}

export default function CapacityPlanPage() {
  const [lines, setLines] = useState<ProductionLineInput[]>(defaultLines());
  const [gypsumCapTpd, setGypsumCapTpd] = useState(1500);
  const [ratioLow, setRatioLow] = useState(4);
  const [ratioHigh, setRatioHigh] = useState(5);
  const [result, setResult] = useState<CapacityPlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateLine = (index: number, patch: Partial<ProductionLineInput>) => {
    setLines((prev) =>
      prev.map((line, i) => (i === index ? { ...line, ...patch } : line)),
    );
  };

  const addLine = () => {
    setLines((prev) => [
      ...prev,
      {
        id: `line_${prev.length + 1}`,
        name: `新增支路 ${prev.length + 1}`,
        requestedP2o5Tpd: 50,
        priority: 1,
      },
    ]);
  };

  const removeLine = (index: number) => {
    setLines((prev) => prev.filter((_, i) => i !== index));
  };

  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await simulateCapacityPlan({
        lines,
        gypsumCapTpd,
        gypsumRatioLow: ratioLow,
        gypsumRatioHigh: ratioHigh,
      });
      setResult(response);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "计算请求失败，请检查后端服务是否已启动。");
    } finally {
      setLoading(false);
    }
  };

  const chartData = useMemo(() => {
    if (!result) return [];
    const lineIds = result.options[0]?.lines.map((line) => line.id) ?? [];
    return lineIds.map((lineId) => {
      const row: Record<string, string | number> = {
        name:
          result.options[0]?.lines.find((line) => line.id === lineId)?.name ??
          lineId,
      };
      for (const option of result.options) {
        const allocation = option.lines.find((line) => line.id === lineId);
        row[option.label] = allocation?.allocatedP2o5Tpd ?? 0;
      }
      return row;
    });
  }, [result]);

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">以渣定产 · 园区物料平衡仿真</h1>
        <p className="text-sm text-foreground/70">
          给定磷石膏消纳能力上限与各支路请求处理量，判断是否超限，超限时给出三种压减方案供参考——
          不是自动下发的排产指令，最终决策仍由生产调度人员完成。
        </p>
      </header>

      <section className="flex flex-col gap-4 rounded-lg border border-foreground/10 p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-medium">各支路请求处理量</h2>
          <button
            type="button"
            onClick={addLine}
            className="rounded border border-foreground/20 px-3 py-1 text-sm hover:bg-foreground/5"
          >
            + 新增支路
          </button>
        </div>

        <div className="flex flex-col gap-3">
          {lines.map((line, index) => (
            <div
              key={index}
              className="grid grid-cols-[1fr_140px_100px_auto] items-center gap-3"
            >
              <input
                value={line.name}
                onChange={(e) => updateLine(index, { name: e.target.value })}
                className="rounded border border-foreground/20 bg-transparent px-2 py-1 text-sm"
                placeholder="支路名称"
              />
              <input
                type="number"
                value={line.requestedP2o5Tpd}
                onChange={(e) =>
                  updateLine(index, { requestedP2o5Tpd: Number(e.target.value) })
                }
                className="rounded border border-foreground/20 bg-transparent px-2 py-1 text-sm"
                placeholder="请求量(吨P2O5/天)"
              />
              <input
                type="number"
                value={line.priority}
                onChange={(e) =>
                  updateLine(index, { priority: Number(e.target.value) })
                }
                className="rounded border border-foreground/20 bg-transparent px-2 py-1 text-sm"
                placeholder="优先级"
              />
              <button
                type="button"
                onClick={() => removeLine(index)}
                className="text-sm text-foreground/50 hover:text-red-500"
              >
                删除
              </button>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-4 border-t border-foreground/10 pt-4">
          <label className="flex flex-col gap-1 text-sm">
            磷石膏消纳能力上限（吨/天）
            <input
              type="number"
              value={gypsumCapTpd}
              onChange={(e) => setGypsumCapTpd(Number(e.target.value))}
              className="rounded border border-foreground/20 bg-transparent px-2 py-1"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            产出系数下限（吨石膏/吨P2O5）
            <input
              type="number"
              value={ratioLow}
              onChange={(e) => setRatioLow(Number(e.target.value))}
              className="rounded border border-foreground/20 bg-transparent px-2 py-1"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            产出系数上限（吨石膏/吨P2O5）
            <input
              type="number"
              value={ratioHigh}
              onChange={(e) => setRatioHigh(Number(e.target.value))}
              className="rounded border border-foreground/20 bg-transparent px-2 py-1"
            />
          </label>
        </div>

        <button
          type="button"
          onClick={runSimulation}
          disabled={loading || lines.length === 0}
          className="w-fit rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "计算中…" : "运行仿真"}
        </button>

        {error && (
          <p className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
      </section>

      {result && (
        <section className="flex flex-col gap-6">
          <div
            className={`rounded-lg border p-4 text-sm ${
              result.requestWithinCap
                ? "border-green-300 bg-green-50 text-green-800"
                : "border-amber-300 bg-amber-50 text-amber-800"
            }`}
          >
            {result.requestWithinCap
              ? `请求处理量共 ${result.totalRequestedP2o5Tpd} 吨P2O5/天，预计磷石膏产出 ${result.requestedGypsumOutputLowTpd}–${result.requestedGypsumOutputHighTpd} 吨/天，在消纳能力上限（${result.gypsumCapTpd} 吨/天）内，无需压减。`
              : `请求处理量共 ${result.totalRequestedP2o5Tpd} 吨P2O5/天，预计磷石膏产出 ${result.requestedGypsumOutputLowTpd}–${result.requestedGypsumOutputHighTpd} 吨/天，超出消纳能力上限（${result.gypsumCapTpd} 吨/天），以下给出三种压减方案供参考。`}
          </div>

          <CapacityGauge
            requestedLowTpd={result.requestedGypsumOutputLowTpd}
            requestedHighTpd={result.requestedGypsumOutputHighTpd}
            capTpd={result.gypsumCapTpd}
            withinCap={result.requestWithinCap}
          />

          {chartData.length > 0 && (
            <div className="h-80 rounded-lg border border-foreground/10 p-4">
              <h3 className="mb-2 text-sm font-medium">各方案下每条支路的分配处理量</h3>
              <ResponsiveContainer width="100%" height="90%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    label={{
                      value: "吨P2O5/天",
                      angle: -90,
                      position: "insideLeft",
                      fontSize: 12,
                    }}
                  />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {result.options.map((option) => (
                    <Bar
                      key={option.label}
                      dataKey={option.label}
                      fill={STRATEGY_COLORS[option.strategy] ?? "#6b7280"}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="overflow-x-auto rounded-lg border border-foreground/10">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-foreground/10 text-left text-foreground/60">
                  <th className="px-3 py-2">方案</th>
                  <th className="px-3 py-2">总分配处理量</th>
                  <th className="px-3 py-2">预计磷石膏产出</th>
                  <th className="px-3 py-2">消纳能力利用率</th>
                  <th className="px-3 py-2">是否在上限内</th>
                </tr>
              </thead>
              <tbody>
                {result.options.map((option) => (
                  <tr key={option.label} className="border-b border-foreground/5">
                    <td className="px-3 py-2">{option.label}</td>
                    <td className="px-3 py-2">
                      {option.totalAllocatedP2o5Tpd.toFixed(1)} 吨P2O5/天
                    </td>
                    <td className="px-3 py-2">
                      {option.gypsumOutputLowTpd.toFixed(0)}–
                      {option.gypsumOutputHighTpd.toFixed(0)} 吨/天
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 overflow-hidden rounded-full bg-foreground/10">
                          <div
                            className={`h-full rounded-full ${
                              option.utilizationPct > 100 ? "bg-red-500" : "bg-accent"
                            }`}
                            style={{ width: `${Math.min(option.utilizationPct, 100)}%` }}
                          />
                        </div>
                        <span>{option.utilizationPct.toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      {option.withinCap ? (
                        <span className="text-green-700">是</span>
                      ) : (
                        <span className="text-red-600">否</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="rounded border border-foreground/10 bg-foreground/[0.03] px-3 py-2 text-xs text-foreground/60">
            数据来源披露：{result.disclosure}
          </p>
        </section>
      )}
    </main>
  );
}
