"use client";

import { fetchMetalDosingScenario } from "@/lib/api-client";
import { SoftSensorReport } from "@/components/soft-sensor-report";

export default function MetalDosingPage() {
  return (
    <SoftSensorReport
      title="金属盐投加沉淀 · 磷酸铁沉淀方法论验证"
      description={
        <>
          业务逻辑链：净化磷酸(PPA) + FeSO₄ →[pH/温度/投料流量控制]→ 沉淀反应
          H₃PO₄+FeSO₄+2H₂O→FePO₄·2H₂O↓+H₂SO₄+H₂O → 陈化 → 洗涤 → 固液分离 → 磷酸铁成品。
          本页用真实污水厂化学除磷SCADA数据（丹麦Agtrup，CC BY-NC
          3.0，非磷化工数据）验证同一个反应家族（Fe+PO₄→FePO₄沉淀）的控制变量能否解释残留浓度指标，
          方向相反（除磷 vs 合成产品）但沉淀化学机理相同。
        </>
      }
      fetchScenario={fetchMetalDosingScenario}
      chartTitle="测试集：实际磷酸盐浓度 vs 模型预测值（T1_PO4）"
      verdict={() => ({
        label: "效果不错，但有一个提醒要看清楚",
        tone: "caveat",
        plainSummary: (
          <>
            用投药量、温度、流量这些控制参数去猜反应残留浓度，猜得相当准，明显比“直接报一个固定数字”强很多。
            <strong>但有个重要提醒</strong>：这套系统本来就是“磷高了自动多投药”的自动调节装置，
            所以投药量和残留浓度本来就是绑在一起变化的——这个准确度里，有一部分是“系统自己的调节规律”，
            不完全是“模型独立发现了什么新东西”。工程上可以参考，但别把它当成脱离了自动加药系统之外的独立预测能力。
          </>
        ),
      })}
    />
  );
}
