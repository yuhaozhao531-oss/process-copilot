export type FlowStageState = "normal" | "watch" | "alert";

export interface FlowStage {
  id: string;
  icon: string;
  label: string;
  sublabel?: string;
  state?: FlowStageState;
  badge?: string;
}

const STATE_STYLES: Record<FlowStageState, { ring: string; bg: string; badge: string }> = {
  normal: {
    ring: "ring-1 ring-foreground/15",
    bg: "bg-surface",
    badge: "bg-foreground/10 text-foreground/60",
  },
  watch: {
    ring: "ring-2 ring-amber-400",
    bg: "bg-amber-50",
    badge: "bg-amber-500 text-white",
  },
  alert: {
    ring: "ring-2 ring-red-500",
    bg: "bg-red-50",
    badge: "bg-red-600 text-white",
  },
};

function StageCard({ stage }: { stage: FlowStage }) {
  const style = STATE_STYLES[stage.state ?? "normal"];
  return (
    <div
      className={`flex min-w-[132px] flex-1 flex-col items-center gap-1 rounded-xl ${style.ring} ${style.bg} px-3 py-3 text-center shadow-sm`}
    >
      <span className="text-2xl leading-none">{stage.icon}</span>
      <span className="text-sm font-medium leading-tight">{stage.label}</span>
      {stage.sublabel && (
        <span className="text-xs leading-tight text-foreground/55">{stage.sublabel}</span>
      )}
      {stage.badge && (
        <span className={`mt-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${style.badge}`}>
          {stage.badge}
        </span>
      )}
    </div>
  );
}

export interface LeadTimeCallout {
  fromLabel: string;
  toLabel: string;
  detail: string;
}

export function ProcessFlowDiagram({
  title,
  stages,
  leadTime,
}: {
  title?: string;
  stages: FlowStage[];
  leadTime?: LeadTimeCallout;
}) {
  return (
    <div className="flex flex-col gap-4 rounded-xl border border-foreground/10 bg-surface/60 p-4">
      {title && <h3 className="text-sm font-medium text-foreground/70">{title}</h3>}
      <div className="flex flex-wrap items-stretch gap-2 sm:flex-nowrap">
        {stages.map((stage, i) => (
          <div key={stage.id} className="flex flex-1 items-center gap-2">
            <StageCard stage={stage} />
            {i < stages.length - 1 && (
              <span className="hidden shrink-0 text-xl text-foreground/25 sm:inline">→</span>
            )}
          </div>
        ))}
      </div>
      {leadTime && (
        <div className="flex items-center gap-3 rounded-lg border border-dashed border-amber-400/70 bg-amber-50/70 px-4 py-2.5 text-sm text-amber-900">
          <span className="font-medium">{leadTime.fromLabel}</span>
          <span className="flex-1 border-t border-dashed border-amber-400" />
          <span className="rounded-full bg-amber-500 px-2.5 py-0.5 text-xs font-semibold text-white">
            {leadTime.detail}
          </span>
          <span className="flex-1 border-t border-dashed border-amber-400" />
          <span className="font-medium">{leadTime.toLabel}</span>
        </div>
      )}
    </div>
  );
}
