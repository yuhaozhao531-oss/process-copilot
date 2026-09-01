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
      renderConclusion={(data) => (
        <>
          诚实结果：R²={data.testR2.toFixed(2)}，明显优于朴素基线，是这几个方法论验证场景里最强的正向结果。
          但要澄清因果方向——投药量（METAL_Q）是最强特征且正相关，这大概率是因为这套系统采用闭环反馈投加
          （在线磷传感器驱动自动加药，磷高了自动多投），高R²里有一部分反映的是控制系统自身的耦合，
          不是纯粹从工艺物理规律里挖出的独立预测能力。
        </>
      )}
    />
  );
}
