# Excel Reference — Spreadsheet Design for create_excel

## Sheet Organization

- **Sheet 1**: Always "Summary" or "Dashboard" — key metrics and totals at a glance
- **Sheet 2+**: Detail sheets organized by category, time period, or data domain
- **Sheet names**: Max 31 characters, descriptive, no special characters except spaces and hyphens
- **Tab order**: General to specific, summary to detail, chronological
- **Rule**: If a workbook has more than 5 sheets, include a "Table of Contents" sheet

## Header Design

The `create_excel` tool automatically bolds headers. Make them count:
- **Short but descriptive**: "Revenue ($M)" not just "Revenue"
- **Include units in headers**: "Weight (kg)", "Price (USD)", "Growth (%)"
- **Avoid abbreviations** unless universally understood (Q1, YTD, ROI)
- **Consistent naming**: If one sheet says "Revenue" another should not say "Sales" for the same metric

## Data Layout Patterns

### Financial Report
```json
{
  "name": "Financial Summary",
  "headers": ["Category", "Q1", "Q2", "Q3", "Q4", "YTD Total", "YoY Change (%)"],
  "rows": [
    ["Revenue", 2500000, 2750000, 2900000, 3100000, 11250000, 12.5],
    ["COGS", 1500000, 1600000, 1700000, 1800000, 6600000, 8.2],
    ["Gross Profit", 1000000, 1150000, 1200000, 1300000, 4650000, 18.3],
    ["Operating Expenses", 600000, 620000, 650000, 680000, 2550000, 5.1],
    ["Net Income", 400000, 530000, 550000, 620000, 2100000, 35.5]
  ]
}
```

### Project Tracker
```json
{
  "name": "Project Tasks",
  "headers": ["Task", "Owner", "Status", "Priority", "Start Date", "Due Date", "% Complete"],
  "rows": [
    ["Design mockups", "Sarah", "Complete", "High", "2026-01-15", "2026-01-30", 100],
    ["Backend API", "James", "In Progress", "High", "2026-01-20", "2026-02-15", 65],
    ["Testing", "Maria", "Not Started", "Medium", "2026-02-10", "2026-02-28", 0]
  ]
}
```

### Dashboard / Summary Sheet
```json
{
  "name": "Dashboard",
  "headers": ["Metric", "Current", "Previous", "Change", "Target", "Status"],
  "rows": [
    ["Monthly Revenue", "$3.1M", "$2.9M", "+6.9%", "$3.0M", "On Track"],
    ["Active Users", "45,230", "42,100", "+7.4%", "44,000", "Above Target"],
    ["Churn Rate", "2.1%", "2.4%", "-0.3pp", "<2.5%", "On Track"],
    ["NPS Score", "72", "68", "+4", "70", "Above Target"]
  ]
}
```

### Comparison Matrix
```json
{
  "name": "Feature Comparison",
  "headers": ["Feature", "Our Product", "Competitor A", "Competitor B", "Industry Avg"],
  "rows": [
    ["Price ($/mo)", 49, 79, 59, 62],
    ["Storage (GB)", 100, 50, 75, 75],
    ["API Access", "Yes", "Premium Only", "Yes", "-"],
    ["Support", "24/7", "Business Hours", "24/7", "-"]
  ]
}
```

## Data Formatting Rules

| Data Type | Format | Example |
|-----------|--------|---------|
| Currency | $X,XXX.XX | $1,234.56 |
| Large currency | $X.XM or $X.XB | $2.5M |
| Percentage | XX.X% | 15.3% |
| Integer | X,XXX | 45,230 |
| Date | YYYY-MM-DD | 2026-02-10 |
| Status | Capitalized label | "Complete", "In Progress", "Not Started" |
| Boolean | "Yes" / "No" | Not checkmarks or 1/0 |
| Empty/missing | "N/A" or "-" | Never leave blank in reports |

## Multi-Sheet Workbook Pattern

For comprehensive reports, use this sheet structure:
1. **Summary** — 3-5 KPIs, high-level totals, status indicators
2. **Detail Data** — Full dataset with all columns
3. **Analysis** — Aggregated views, comparisons, trends
4. **Reference** — Lookup tables, definitions, methodology notes
