"""一次性预处理脚本：把 Kaggle 铁矿浮选原始CSV（737453行，20秒采样）
聚合成按小时分组的小文件，提交进仓库；原始CSV不提交（175MB，且是外部
公开数据，不是本项目产出物）。

用法：
    python scripts/prep_flotation_data.py data/MiningProcess_Flotation_Plant_Database.csv

聚合逻辑：CSV里的 date 列本身就是小时桶标签（同一小时内约180行共享
同一个 date 值，化验值在小时内保持不变——这就是"实时传感器每20秒采样，
化验结果每小时更新一次"的滞后结构，见报告3.2节"漏洞一"）。按 date 分组，
连续型传感器变量取组内均值，化验值直接取（组内本就相同）。

数据来源：Kaggle "Quality Prediction in a Mining Process"
(edumagalhaes/quality-prediction-in-a-mining-process)，CC0协议，真实
巴西某铁矿浮选厂数据，2017年3-9月。这是结构相似的真实工业数据，
不是磷化工数据，更不是息烽园区数据。
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

SENSOR_COLUMNS = [
    "% Iron Feed",
    "% Silica Feed",
    "Starch Flow",
    "Amina Flow",
    "Ore Pulp Flow",
    "Ore Pulp pH",
    "Ore Pulp Density",
    "Flotation Column 01 Air Flow",
    "Flotation Column 02 Air Flow",
    "Flotation Column 03 Air Flow",
    "Flotation Column 04 Air Flow",
    "Flotation Column 05 Air Flow",
    "Flotation Column 06 Air Flow",
    "Flotation Column 07 Air Flow",
    "Flotation Column 01 Level",
    "Flotation Column 02 Level",
    "Flotation Column 03 Level",
    "Flotation Column 04 Level",
    "Flotation Column 05 Level",
    "Flotation Column 06 Level",
    "Flotation Column 07 Level",
]
TARGET_COLUMN = "% Silica Concentrate"
OUTPUT_COLUMNS = ["hour", *SENSOR_COLUMNS, TARGET_COLUMN]


def _to_float(raw: str) -> float:
    return float(raw.replace(",", "."))


def aggregate(input_path: Path) -> list[dict[str, float | str]]:
    sums: dict[str, list[float]] = {}
    counts: dict[str, int] = {}
    order: list[str] = []
    target_value: dict[str, float] = {}

    with input_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            hour = row["date"]
            if hour not in sums:
                sums[hour] = [0.0] * len(SENSOR_COLUMNS)
                counts[hour] = 0
                order.append(hour)
            for i, column in enumerate(SENSOR_COLUMNS):
                sums[hour][i] += _to_float(row[column])
            counts[hour] += 1
            target_value[hour] = _to_float(row[TARGET_COLUMN])

    records: list[dict[str, float | str]] = []
    for hour in order:
        count = counts[hour]
        record: dict[str, float | str] = {"hour": hour}
        for i, column in enumerate(SENSOR_COLUMNS):
            record[column] = sums[hour][i] / count
        record[TARGET_COLUMN] = target_value[hour]
        records.append(record)
    return records


def write_output(records: list[dict[str, float | str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(record)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/prep_flotation_data.py <raw_csv_path>", file=sys.stderr)
        return 2
    input_path = Path(sys.argv[1])
    output_path = Path(__file__).resolve().parents[1] / "data" / "flotation_hourly.csv"
    records = aggregate(input_path)
    write_output(records, output_path)
    print(f"wrote {len(records)} hourly rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
