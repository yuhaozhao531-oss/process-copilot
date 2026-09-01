export interface ProductionLineInput {
  id: string;
  name: string;
  requestedP2o5Tpd: number;
  priority: number;
}

export interface LineAllocation {
  id: string;
  name: string;
  requestedP2o5Tpd: number;
  allocatedP2o5Tpd: number;
  loadPctOfRequest: number;
}

export interface CapacityPlanOption {
  strategy: "proportional" | "priority_first" | "equal_share";
  label: string;
  lines: LineAllocation[];
  totalAllocatedP2o5Tpd: number;
  gypsumOutputLowTpd: number;
  gypsumOutputHighTpd: number;
  withinCap: boolean;
  utilizationPct: number;
}

export interface CapacityPlanResponse {
  gypsumCapTpd: number;
  totalRequestedP2o5Tpd: number;
  requestedGypsumOutputLowTpd: number;
  requestedGypsumOutputHighTpd: number;
  requestWithinCap: boolean;
  options: CapacityPlanOption[];
  disclosure: string;
}

export interface VariableSpec {
  variableId: string;
  variableName: string;
  unit: string;
  monitoringPoint: string;
  leadingIndicator: boolean;
}

export interface EarlyWarningResult {
  triggered: boolean;
  warningDay: number | null;
  warningVariableId: string | null;
  breachDay: number | null;
  breachVariableId: string;
  leadTimeDays: number | null;
  summary: string;
}

export interface LeachateScenarioResponse {
  series: {
    dayIndex: number[];
    series: Record<string, number[]>;
  };
  earlyWarning: EarlyWarningResult;
  variables: VariableSpec[];
  citations: { label: string; detail: string }[];
  regulatoryLimitMgL: number;
  disclosure: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function simulateCapacityPlan(input: {
  lines: ProductionLineInput[];
  gypsumCapTpd: number;
  gypsumRatioLow?: number;
  gypsumRatioHigh?: number;
}): Promise<CapacityPlanResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/capacity-plan/simulate`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input),
    },
  );

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(
      `计算请求失败（${response.status}）：${body}`,
      response.status,
    );
  }

  return (await response.json()) as CapacityPlanResponse;
}

export async function fetchLeachateScenario(
  seed: number = 42,
): Promise<LeachateScenarioResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/environmental-scenarios/jiaoyishan-leachate?seed=${seed}`,
  );

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(
      `场景数据请求失败（${response.status}）：${body}`,
      response.status,
    );
  }

  return (await response.json()) as LeachateScenarioResponse;
}
