# Practical 11: Data Serving, Reverse ETL, and Security

## Aim / Problem Definition
To construct a secure analytical serving platform and Reverse ETL workflow using a local database. The practical implements SHA-256 identity hashing, column-level masking (email, SSN, name), an analyst-safe view, Role-Based Access Control (RBAC), and centralized security audit logging. It also demonstrates Reverse ETL by syncing high-churn risk customer segments into an operational CRM target table.

## Tools / Technologies
- Python 3.13
- SQLite3 (`customer_analytics.db`)
- Pandas & NumPy
- Python standard library (`hashlib`, `re`, `datetime`, `logging`)

## Step-by-Step
1. **Generate Customer Analytical Dataset**: Run `generate_analytics_data.py` to synthesize 1,000 customer records containing PII (`full_name`, `email`, `ssn`), `lifetime_value`, `churn_risk_score`, and `target_segment`.
2. **Apply Identity Hashing & Masking**:
   - Compute deterministic SHA-256 hashes of customer IDs for pseudo-anonymization.
   - Mask emails (`john.smith@example.com` -> `j***h@example.com`) and SSNs (`***-**-6789`).
   - Tokenize names (`John Smith` -> `J*** S***`).
3. **Build Analyst-Safe View**: Create `analyst_safe_view` in SQLite containing only masked columns, hashed IDs, and analytical features, completely concealing raw PII.
4. **Implement Reverse ETL Sync**: Extract high-value customers at churn risk (`churn_risk_score >= 0.60`) from analytics and sync them directly into the operational destination table `operational_crm_targets` with automated action triggers (`Trigger VIP Retention Promo`).
5. **Enforce Role-Based Access Control (RBAC)**: Enforce access policies via an access gateway. Verify that the `ADMIN` role can access raw data, while the `ANALYST` role is permitted to query only `analyst_safe_view` and is blocked from raw PII.
6. **Centralized Security Audit Trail**: Log every database initialization, query execution, access denial, and Reverse ETL sync to `logs/security_audit.log`.

## Output
### Security & Serving Test Results:
- **Synthetic Dataset**: 1,000 records loaded into `customer_analytics.db`.
- **Hashed & Masked Data Sample**:
  - Raw ID: `CUST_00001` -> Hashed ID: `9e4720acf56b4123`
  - Raw Email: `michael.brown1@example.com` -> Masked: `m***1@example.com`
  - Raw SSN: `370-81-6734` -> Masked: `***-**-6734`
- **Reverse ETL Sync**: 22 high-value churn targets synced to `operational_crm_targets` (snapshot in `results/reverse_etl_crm_export.csv`).
- **RBAC Enforcement**:
  - `ADMIN` role: Access granted to raw table.
  - `ANALYST` role (safe view): Access granted to masked records.
  - `ANALYST` role (raw table): Access **DENIED** with policy violation error.
- **Audit Log (`logs/security_audit.log`)**: Active audit trail recording timestamps, roles, resources, actions, and security status.

## Key Questions

### 1. What is Reverse ETL and why is it increasingly important in enterprise data architectures?
Traditional ETL moves operational data into analytical warehouses for reporting. **Reverse ETL** reverses this flow: it extracts operational insights, scores, and segments computed in the data warehouse (such as customer churn probability, lead scores, or lifetime value) and syncs them directly back into operational tools (like Salesforce, HubSpot, Zendesk, or marketing databases) so business teams can take immediate action.

### 2. Differentiate between data masking, tokenization, and hashing.
- **Data Masking**: Obfuscates parts of a sensitive string while preserving its visual format for display (e.g. `***-**-6789` or `j***h@example.com`). It is typically irreversible.
- **Tokenization**: Replaces sensitive data with a non-sensitive substitute (token) that maps back to the original value via a secure token vault.
- **Hashing**: A one-way cryptographic mathematical function (e.g., SHA-256) that converts input into a fixed-length string. It cannot be reversed, making it ideal for anonymized record linkage.

### 3. How do database views and RBAC protect Personally Identifiable Information (PII)?
Database views expose a virtual table with restricted column projections (omitting sensitive raw PII like SSNs or plain text emails). When combined with Role-Based Access Control (RBAC), permissions to the underlying physical table are restricted to privileged administrators, while analysts and third-party tools are granted read-only access exclusively to the sanitized view, preventing accidental PII exposure and ensuring compliance with regulations like GDPR.

## Supplementary Problem: Analyst Role Restriction
**Requirement**: Complete the supplementary analyst-role restriction to masked/tokenized identity fields.

**Implementation & Result**:
- The RBAC gateway inspects queries submitted by users in the `ANALYST` role.
- When an analyst attempts to query the physical `customer_analytics` table, the gateway immediately halts execution, raises a `PermissionError`, and logs a security policy violation in `logs/security_audit.log`.
- When an analyst queries `analyst_safe_view`, the query executes successfully and returns only hashed IDs and masked contact details.
- **Result**: Complete isolation of sensitive customer PII from unauthorized roles.

## Conclusion
Practical 11 demonstrated how to implement modern data serving patterns with robust security undercurrents. Column-level masking, SHA-256 hashing, and role-based view restrictions ensure full compliance and privacy protection, while Reverse ETL bridges the gap between analytical intelligence and operational business execution.

## Screenshot List
- **Screenshot 1 – Database Initialization & Masking**: Terminal output showing database setup and hashed/masked samples.  
  *Where to place it*: Under Step-by-Step section.
- **Screenshot 2 – Reverse ETL Operational Sync**: Terminal output showing 22 high-value churn targets synced to `operational_crm_targets`.  
  *Where to place it*: Under Output section.
- **Screenshot 3 – RBAC Access Denial Test**: Terminal output showing `[DENIED] Security Policy: Role 'ANALYST' cannot query raw 'customer_analytics' table`.  
  *Where to place it*: Under Supplementary Problem section.
- **Screenshot 4 – Centralized Security Audit Log**: Contents of `logs/security_audit.log` showing role audit events.  
  *Where to place it*: Under Output section.
