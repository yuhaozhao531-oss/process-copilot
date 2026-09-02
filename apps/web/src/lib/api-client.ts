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

export interface SoftSensorResponse {
  featureNames: string[];
  coefficients: number[];
  intercept: number;
  ridgeAlpha: number;
  trainSize: number;
  testSize: number;
  testMae: number;
  testR2: number;
  naiveBaselineMae: number;
  testHours: string[];
  testActual: number[];
  testPredicted: number[];
  disclosure: string;
}

// Empty string = relative paths, proxied server-side by the rewrite in
// next.config.ts (API_PROXY_TARGET) — avoids the browser making a mixed-content
// (https page -> http backend) request directly.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

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

export async function fetchFlotationScenario(
  trainFraction: number = 0.8,
): Promise<SoftSensorResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/scenarios/flotation-lag-prediction?train_fraction=${trainFraction}`,
  );

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(
      `场景数据请求失败（${response.status}）：${body}`,
      response.status,
    );
  }

  return (await response.json()) as SoftSensorResponse;
}

export async function fetchMetalDosingScenario(
  trainFraction: number = 0.8,
): Promise<SoftSensorResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/scenarios/metal-dosing-precipitation?train_fraction=${trainFraction}`,
  );

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(
      `场景数据请求失败（${response.status}）：${body}`,
      response.status,
    );
  }

  return (await response.json()) as SoftSensorResponse;
}
