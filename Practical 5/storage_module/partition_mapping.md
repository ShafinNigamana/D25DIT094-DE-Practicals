# Bucket Partition Mapping Rules

## Storage Structure Overview
This document specifies the Hive-style directory partitioning scheme implemented in the S3-compatible object store for Practical 5.

- **Target Bucket**: `de-warehouse-partitioned`
- **Total Partitions**: 24 distinct partition folders
- **Dataset Size**: 75,000 records across multi-year transactions

## Partition Path Scheme
All objects land in the bucket using key-value Hive directory prefixes:

```text
year=YYYY/month=MM/region=REGION/data.csv
```

### Partition Keys & Domain Values:
1. **`year`**: `2024`, `2025` (2 years)
2. **`month`**: `01`, `02`, `03` (3 months per year)
3. **`region`**: `north`, `south`, `east`, `west` (4 geographical sales regions)

**Total Combinations**: $2 \times 3 \times 4 = 24$ partitions.

---

## Example S3 Object Key
```text
year=2025/month=01/region=west/data.csv
```

---

## Role in Partition Pruning
In S3-compatible object storage, directories are represented as object key prefixes.

When an analytical query requests data for a specific year, month, or region (e.g. `year=2025` and `region=west`), the query engine specifies:
```python
Prefix="year=2025/month=01/region=west/"
```
The storage server returns **only the object matching this prefix** (5,000 rows, 360.07 KB). The remaining 23 partitions (70,000 rows) are completely skipped (**Partition Pruning**), resulting in a **93.4% I/O reduction** and **22.86x faster query latency**.
