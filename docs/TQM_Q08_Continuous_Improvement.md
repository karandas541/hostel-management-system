# TQM: Q08 — Improve User Satisfaction

## Purpose

This project applies Total Quality Management (TQM) to hostel operations. Its quality goal is **Q08 — Improve User Satisfaction**. It collects student feedback, records complaints and their outcomes, and presents operational measures that can help administrators decide what to improve.

The application supports this goal by making service feedback visible alongside room occupancy, fee completion, and complaint status. It does not claim that a service improved unless a later measurement supports that conclusion.

## Quality Objectives

1. Give students a consistent way to rate hostel service areas and provide comments.
2. Make complaint status and resolution visible to the people responsible for hostel operations and to the student who submitted the complaint.
3. Use actual records to find low-rated service areas and unresolved complaints.
4. Review feedback and operational measures regularly, then plan and evaluate corrective actions.
5. Keep student data private through role-based access and account-to-student ownership checks.

## Feedback Mechanism

The feedback module accepts a 1–5 rating for:

- Room quality
- Cleanliness
- Food quality
- Maintenance
- Wi-Fi
- Security
- Hostel staff
- Common facilities
- Overall experience

Students can also provide comments and select an evaluation period (weekly, monthly, quarterly, or yearly). Feedback is associated with the authenticated student's linked record; the student cannot submit feedback on behalf of a different student.

## Complaint Handling

Complaints are recorded with a category, description, priority, and creation time. Administrators can assign a complaint and update its status. The supported statuses are **Submitted**, **Assigned**, **In Progress**, **Resolved**, and **Closed**. Resolution details and timestamps are stored where applicable. Students can view complaints belonging to their own linked record.

The system currently measures complaint totals, open complaints, resolved/closed complaints, and the resolution rate. Although complaint creation and resolution timestamps exist, an average resolution-time metric is not currently calculated in the dashboard.

## Metrics and Definitions

All figures below are calculated from current database records. Empty datasets are shown as no data or not applicable rather than being represented as measured performance.

| Measure | Calculation / source | Interpretation |
| --- | --- | --- |
| Average satisfaction | Average of `overall_experience` ratings in feedback records | Overall submitted rating on a 1–5 scale |
| Satisfaction by area | Average rating for each feedback category | Helps identify categories with lower or higher reported scores |
| Feedback responses | Count of feedback records | Shows how many feedback submissions underpin the averages |
| Total beds | Sum of room capacities | Configured capacity in the rooms table |
| Occupied beds | Count of active room allocations (`vacated_at` is empty) | Beds currently allocated in the database |
| Available beds | `max(total beds - occupied beds, 0)` | Unallocated configured capacity |
| Occupancy rate | `occupied beds / total beds × 100` when capacity is non-zero | Database allocation rate; it does not verify physical occupancy |
| Fees collected | Sum of recorded payment amounts | Recorded payments, not an external bank reconciliation |
| Fees pending | Sum per fee of `max(fee amount - payments for that fee, 0)` | Outstanding balance after partial payments |
| Fee completion rate | Collected amount divided by total fee amount, capped at 100% | Payment progress across recorded fee amounts; no fees means not applicable |
| Total complaints | Count of complaint records | All complaints currently stored |
| Open complaints | Complaints whose status is neither Resolved nor Closed | Current unresolved workload |
| Resolved/closed complaints | Count of Resolved and Closed records | Complaints with a completed status |
| Complaint resolution rate | Resolved/closed complaints divided by total complaints × 100 | A zero-complaint period is displayed as zero rather than as a measured success rate |

## Improvement Recommendations

Recommendations are derived from the observed average for each feedback category:

- **No feedback yet:** collect feedback before setting a target.
- **Below 3.0:** critical improvement recommendation.
- **3.0 to below 4.0:** needs improvement recommendation.
- **4.0 or higher:** good performance; continue monitoring.

These are application guidance thresholds, not a claim that a formal institutional quality standard has been met. Administrators should review comments and operational context before choosing an action.

## PDCA Continuous Improvement Cycle

The Quality Dashboard presents a Plan–Do–Check–Act (PDCA) guide:

1. **Plan:** Review feedback, complaint categories/statuses, and operational measures; select a specific service issue.
2. **Do:** Apply a corrective action, such as a maintenance follow-up or a service-process change.
3. **Check:** Collect new feedback and review relevant complaint or operations data after the action.
4. **Act:** Keep effective changes as standard practice, or revise the action and begin another cycle.

The current PDCA panel is guidance only. The application does not yet record improvement owners, action dates, or before/after measurements as a formal action register.

## Reporting and Review

Administrators can review satisfaction, improvement areas, operational summaries, and export reports to CSV or PDF. Reports use saved application data. The current project does not calculate a most-common complaint category, average complaint resolution time, or a separate occupancy-accuracy measure; those should be added only with explicit definitions and tested data calculations.

## Data Privacy

- Admins have access to hostel-wide management and analytics.
- Students are limited to the records associated with their authenticated student mapping in supported modules.
- Student dashboard views do not include hostel-wide financial, occupancy, or satisfaction analytics.
- Do not include identifiable student details in presentation screenshots or exported samples unless disclosure is authorized.

## Current Limitations and Next Improvements

- Add a tracked improvement-action register with an owner, planned action, due date, and review date.
- Measure complaint resolution time from stored creation and resolution timestamps, with a clearly defined rule for reopened complaints.
- Add complaint-category frequency reports and appropriate date filters.
- Compare feedback before and after recorded improvement actions without presenting correlation as proof of causation.
- Add comprehensive automated tests for the metric formulas and role-scoped results.
