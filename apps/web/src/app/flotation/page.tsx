"use client";

import { fetchFlotationScenario } from "@/lib/api-client";
import { SoftSensorReport } from "@/components/soft-sensor-report";

export default function FlotationPage() {
  return (
    <SoftSensorReport
      title="浮选投料 · 滞后化验软测量方法论验证"
      description={
        <>
          业务逻辑链：矿石品位波动 → 破碎/磨矿/浮选（加药量、矿浆性质实时传感）→
          精矿浆品位仍波动，滞后1小时才出化验结果。本页验证的边界只到这一步——
          用真实铁矿浮选数据（CC0，非磷化工数据）测试“实时传感器能否预测滞后化验指标”这套方法论，
          不能代表湿法磷酸反应槽萃取段的表现。
        </>
      }
      fetchScenario={fetchFlotationScenario}
      chartTitle="测试集：实际化验值 vs 模型预测值（% Silica Concentrate）"
      renderConclusion={(data) => (
        <>
          诚实结果：{data.testMae <= data.naiveBaselineMae ? "略优于" : "未能优于"}
          朴素基线，不是“AI证明有效”的展示——在这份真实数据上，简单线性模型的滞后预测能力很有限，
          这个结论本身就是有价值的发现。
        </>
      )}
    />
  );
}
