"""一次性预处理脚本：把 Agtrup（丹麦BlueKolding污水厂）化学除磷原始CSV
（525600行，2分钟采样，2021-08~2023-07共2年）聚合成按小时分组的小文件，
提交进仓库；原始CSV不提交（43.7MB，外部公开数据，不是本项目产出物）。

用法：
    python scripts/prep_agtrup_data.py data/agtrup_raw.csv

聚合逻辑：按小时分组取均值，纯粹是为了把数据体量降到可以提交进仓库的
规模，不像浮选数据集那样对应"化验滞后"的真实结构——这里所有变量都是
2分钟采样的连续过程量，没有滞后化验这一说。

数据来源：Mendeley Data "Wastewater Treatment Plant Data for Nutrient
Removal System" (DOI 10.17632/34rpmsxc4z.1)，CC BY-NC 3.0协议，真实
丹麦Agtrup(BlueKolding)污水厂SCADA数据。这是结构相似的真实工业数据
（金属盐投加沉淀磷酸根，跟磷酸铁产品合成同属Fe+PO4→FePO4沉淀反应家族，
只是方向相反：一个是从水里除磷酸根，一个是合成磷酸铁产品），不是磷化工
数据，更不是息烽园区数据；非商业使用需署名。
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

VALUE_COLUMNS = [
    "IN_METAL_Q",
    "T1_O2",
    "METAL_Q",
    "TEMPERATURE",
    "IN_Q",
    "MAX_CF",
    "PROCESSPHASE_INLET",
    "PROCESSPHASE_OUTLET",
    "T1_NH4",
    "T1_PO4",
]
OUTPUT_COLUMNS = ["hour", *VALUE_COLUMNS]


def aggregate(input_path: Path) -> list[dict[str, float | str]]:
    sums: dict[str, list[float]] = {}
    counts: dict[str, int] = {}
    order: list[str] = []

    with input_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            hour = row["date"][:13]  # "YYYY-MM-DD HH"
            if hour not in sums:
                sums[hour] = [0.0] * len(VALUE_COLUMNS)
                counts[hour] = 0
                order.append(hour)
            for i, column in enumerate(VALUE_COLUMNS):
                sums[hour][i] += float(row[column])
            counts[hour] += 1

    records: list[dict[str, float | str]] = []
    for hour in order:
        count = counts[hour]
        record: dict[str, float | str] = {"hour": hour}
        for i, column in enumerate(VALUE_COLUMNS):
            record[column] = sums[hour][i] / count
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
        print("usage: python scripts/prep_agtrup_data.py <raw_csv_path>", file=sys.stderr)
        return 2
    input_path = Path(sys.argv[1])
    output_path = Path(__file__).resolve().parents[1] / "data" / "agtrup_hourly.csv"
    records = aggregate(input_path)
    write_output(records, output_path)
    print(f"wrote {len(records)} hourly rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
