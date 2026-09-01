"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ApiError,
  fetchFlotationScenario,
  type SoftSensorResponse,
} from "@/lib/api-client";

export default function FlotationPage() {
  const [data, setData] = useState<SoftSensorResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch-on-mount pattern, no Suspense boundary set up for this demo page
    setLoading(true);
    setError(null);
    fetchFlotationScenario()
      .then(setData)
      .catch((err) =>
        setError(
          err instanceof ApiError
            ? err.message
            : "场景数据加载失败，请检查后端服务是否已启动。",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  const chartData = useMemo(() => {
    if (!data) return [];
    return data.testHours.map((hour, i) => ({
      hour: hour.slice(5, 13), // MM-DD HH
      实际值: data.testActual[i],
      预测值: data.testPredicted[i],
    }));
  }, [data]);

  const topFeatures = useMemo(() => {
    if (!data) return [];
    return data.featureNames
      .map((name, i) => ({ name, coefficient: data.coefficients[i] }))
      .sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient))
      .slice(0, 6);
  }, [data]);

  const beatsBaseline = data ? data.testMae <= data.naiveBaselineMae : false;

  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold">浮选投料 · 滞后化验软测量方法论验证</h1>
        <p className="text-sm text-foreground/70">
          业务逻辑链：矿石品位波动 → 破碎/磨矿/浮选（加药量、矿浆性质实时传感）→
          精矿浆品位仍波动，滞后1小时才出化验结果。本页验证的边界只到这一步——
          用真实铁矿浮选数据（CC0，非磷化工数据）测试“实时传感器能否预测滞后化验指标”这套方法论，
          不能代表湿法磷酸反应槽萃取段的表现。
        </p>
      </header>

      {loading && <p className="text-sm text-foreground/50">加载中…</p>}
      {error && (
        <p className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {data && (
        <>
          <div
            className={`rounded-lg border p-4 text-sm ${
              beatsBaseline
                ? "border-blue-300 bg-blue-50 text-blue-900"
                : "border-amber-300 bg-amber-50 text-amber-900"
            }`}
          >
            <p className="font-medium">
              诚实结果：{beatsBaseline ? "略优于" : "未能优于"}朴素基线，不是“AI证明有效”的展示。
            </p>
            <p className="mt-1 text-foreground/70">
              训练集 {data.trainSize} 小时 / 测试集 {data.testSize}{" "}
              小时（按时间先后切分，不随机打乱）；Ridge正则化强度 α=
              {data.ridgeAlpha}（训练集内部交叉验证选出，不是拿测试集调的）。
              测试集MAE = {data.testMae.toFixed(4)}，朴素基线（永远预测训练集均值）MAE ={" "}
              {data.naiveBaselineMae.toFixed(4)}，R² = {data.testR2.toFixed(4)}
              ——在这份真实数据上，简单线性模型的滞后预测能力很有限，这个结论本身就是有价值的发现。
            </p>
          </div>

          <div className="h-80 rounded-lg border border-foreground/10 p-4">
            <h3 className="mb-2 text-sm font-medium">
              测试集：实际化验值 vs 模型预测值（% Silica Concentrate）
            </h3>
            <ResponsiveContainer width="100%" height="90%">
              <LineChart data={chartData} margin={{ top: 4, right: 12, left: 0, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="hour" tick={{ fontSize: 10 }} interval={Math.floor(chartData.length / 10)} />
                <YAxis tick={{ fontSize: 10 }} width={44} />
                <Tooltip />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="实际值" stroke="#111827" dot={false} strokeWidth={1.5} />
                <Line type="monotone" dataKey="预测值" stroke="#2563eb" dot={false} strokeWidth={1.5} strokeDasharray="4 2" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="overflow-x-auto rounded-lg border border-foreground/10">
            <table className="w-full min-w-[480px] text-sm">
              <thead>
                <tr className="border-b border-foreground/10 text-left text-foreground/60">
                  <th className="px-3 py-2">影响最大的传感变量（按标准化系数绝对值排序）</th>
                  <th className="px-3 py-2">标准化系数</th>
                </tr>
              </thead>
              <tbody>
                {topFeatures.map((feature) => (
                  <tr key={feature.name} className="border-b border-foreground/5">
                    <td className="px-3 py-2">{feature.name}</td>
                    <td className="px-3 py-2">
                      <span className={feature.coefficient >= 0 ? "text-green-700" : "text-red-600"}>
                        {feature.coefficient.toFixed(4)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="rounded border border-foreground/10 bg-foreground/[0.03] px-3 py-2 text-xs text-foreground/60">
            数据来源披露：{data.disclosure}
          </p>
        </>
      )}
    </main>
  );
}
