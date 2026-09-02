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
      flowStages={[
        { id: "ore", icon: "⛏️", label: "矿石品位波动", sublabel: "入选原矿" },
        { id: "process", icon: "🌀", label: "破碎/磨矿/浮选", sublabel: "加药量、矿浆性质实时传感" },
        { id: "predict", icon: "🤖", label: "岭回归模型预测", sublabel: "本页验证的边界" },
        { id: "lab", icon: "🧪", label: "化验室出结果", sublabel: "滞后约1小时" },
      ]}
      chartTitle="测试集：实际化验值 vs 模型预测值（% Silica Concentrate）"
      verdict={(data) => ({
        label: "效果不理想，还不能用",
        tone: "weak",
        plainSummary: (
          <>
            用传感器数据提前“猜”化验结果，猜出来的准确度只比“什么都不看、直接报一个固定数字”稍微好一点点，
            算不上真的猜得准。换句话说，这套方法在这份数据上目前还不靠谱，不建议拿它替代人工化验或者作为判断依据。
            {data.testMae <= data.naiveBaselineMae
              ? "（严格说比瞎猜略强，但强得很有限。）"
              : "（甚至没比瞎猜强。）"}
          </>
        ),
      })}
    />
  );
}
