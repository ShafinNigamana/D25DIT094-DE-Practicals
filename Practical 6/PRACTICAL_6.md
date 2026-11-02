# Practical 6: Storage Lifecycle Management

## Aim / Problem Definition
To implement and verify Hot, Warm, and Cold storage lifecycle policies using MinIO S3 object storage, JSON lifecycle policies, and Python automation. To simulate object age, evaluate access frequency rules, automatically detect objects inactive for more than 90 days, execute tier demotion, and produce a cost/benefit comparison between unmanaged storage and tiered lifecycle management.

## Tools / Technologies
- MinIO (S3-compatible distributed object storage in Docker)
- Docker Desktop
- Python 3.13 (`boto3`)
- JSON (S3 Lifecycle Configuration specifications)
- Pandas

## Step-by-Step
1. **Start MinIO Service**: Ensure MinIO container is running on `localhost:9000`.
2. **Define Lifecycle Configuration**: Create `lifecycle_policy.json` declaring rules:
   - Transition objects to Warm storage after 30 days.
   - Transition objects to Cold archive after 90 days.
   - Expire/delete temporary logs after 365 days.
3. **Apply Policy**: Use Boto3 `put_bucket_lifecycle_configuration` to register the lifecycle policy on dedicated test bucket `de-lifecycle-test`.
4. **Synthesize Objects Across Tiers**: Upload test files with varying simulated age and access profiles (Hot active files, Warm medium-access files, and Cold inactive archives).
5. **Evaluate Age and Inactivity Rules**: Run `storage_lifecycle_manager.py` to inspect metadata and access frequency, flagging objects unaccessed for $> 90$ days.
6. **Execute Tier Demotion**: Demote inactive objects to Cold archive and tag them accordingly.
7. **Calculate Cost/Benefit Savings**: Compare standard Hot storage pricing against tiered Hot/Warm/Cold pricing.

## Output
- **Applied Lifecycle Policy**: Valid JSON specification in `lifecycle_policy.json`.
- **Object Evaluation Catalog (`results/lifecycle_evaluation.csv`)**: Details age, access counts, and policy transition recommendations for every object.
- **Cost / Benefit Comparison (`results/cost_benefit_comparison.csv`)**:
  - Unmanaged Storage (100% Hot): $0.023 / GB / month.
  - Automated Lifecycle Tiering: Drops monthly spend by over 70% by moving 90+ day inactive datasets to Cold Glacier-equivalent storage ($0.00099 / GB).

## Key Questions

### 1. What are the key characteristics of Hot, Warm, and Cold storage tiers?
- **Hot Tier (e.g., S3 Standard)**: High throughput, immediate sub-millisecond retrieval, no minimum retention period, highest storage cost. Used for active transactions and frequently queried data.
- **Warm Tier (e.g., S3 Standard-IA)**: Low storage cost, slight per-GB retrieval fee, 30-day minimum retention. Used for monthly backups and infrequent reporting.
- **Cold Tier (e.g., S3 Glacier Deep Archive)**: Lowest storage cost, retrieval delay of minutes to hours, 90-180 day minimum retention. Used for legal compliance, long-term archival, and disaster recovery.

### 2. Why should storage lifecycle policies be automated rather than managed manually?
Manual cleanup is error-prone, labor-intensive, and rarely scales with exponential enterprise data growth. Automated lifecycle rules continuously enforce retention and deletion policies behind the scenes, ensuring compliance with privacy regulations (like GDPR data deletion mandates) and preventing runaway cloud storage bills.

### 3. What trade-offs must be evaluated before moving objects to Cold archive tiers?
1. **Retrieval Latency**: Cold objects cannot be read instantaneously; retrieval may take 3 to 12 hours.
2. **Retrieval Costs**: High per-GB data egress and retrieval request fees.
3. **Minimum Storage Durations**: Deleting or modifying objects before the 90 or 180-day minimum incurs early deletion penalties.

## Supplementary Problem: 90-Day Inactivity Detection & Demotion Utility
**Requirement**: Complete the supplementary 90-day inactivity/demotion utility and cost/benefit comparison.

**Implementation & Result**:
- The utility scans object metadata and identifies objects with `access_count_30d == 0` and `days_old > 90`.
- Objects such as `historical/q1_financial_audit.parquet` and `historical/legacy_user_archive_2025.tar.gz` were detected as inactive and immediately demoted to `COLD (Archive)`.
- **Cost Analysis**: Demonstrated a **~75% cost reduction** compared to leaving unaccessed historical archives in Hot storage.
- Results saved to `results/lifecycle_evaluation.csv` and `results/cost_benefit_comparison.csv`.

## Conclusion
Practical 6 demonstrated how storage lifecycle management balances performance and cloud expenditure. By systematically transitioning aging datasets from Hot to Warm and Cold tiers, and pruning unneeded temporary files, organizations minimize storage overhead while maintaining data availability.

## Screenshot List
- **Screenshot 1 – Lifecycle Policy JSON**: Code snippet of `lifecycle_policy.json`.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 2 – MinIO Bucket & Test Objects**: MinIO Console view of bucket `de-lifecycle-test` and uploaded files.  
  *Where to place it*: Under Output section.
- **Screenshot 3 – 90-Day Inactivity Detection**: Terminal output of `storage_lifecycle_manager.py` showing inactive objects flagged for demotion.  
  *Where to place it*: Under Supplementary Problem section.
- **Screenshot 4 – Cost/Benefit Comparison Table**: Terminal output of cost comparison showing percentage savings.  
  *Where to place it*: Under Output section.
