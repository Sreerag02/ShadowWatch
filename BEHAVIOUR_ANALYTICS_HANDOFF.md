\# ShadowWatch Behaviour Analytics Handoff



\## 1. Scope



Implemented and integrated the behavioural analytics module for:



\- R006 — Repetitive / Copied Investigation Notes

\- R007 — Investigation Duration Anomaly

\- R008 — Repeat Incident Pattern

\- R009 — Combined Suspicious Investigation Behaviour



The implementation uses the existing operational database schema and produces explainable findings.



\---



\## 2. R006 — Repetitive Investigation



\### Method



\- TF-IDF vectorization

\- Cosine similarity

\- Internal repeated-text detection



\### Prototype threshold



\- Similarity threshold: 0.90



\### Metro Telecom validation



\- Expected: 6

\- Predicted: 6

\- True Positives: 6

\- False Positives: 0

\- False Negatives: 0

\- Precision: 1.0000

\- Recall: 1.0000

\- F1 Score: 1.0000



R006 successfully detected the repetitive investigation pattern in the expected cases.



\---



\## 3. R007 — Investigation Duration Anomaly



\### Method



Investigation duration is calculated as:



completed\_at - started\_at



The duration is compared against a severity-specific baseline rather than using one universal duration threshold.



R007 uses investigation timestamps and is separate from R004:



\- R004: case opened\_at -> closed\_at

\- R007: investigation started\_at -> completed\_at



\### Metro Telecom validation



\- Ground-truth records: 5

\- Observable cases: 3

\- Predicted: 3

\- True Positives: 3

\- False Positives: 0

\- False Negatives: 0

\- Precision: 1.0000

\- Recall: 1.0000

\- F1 Score: 1.0000



Two ground-truth cases were unobservable because they did not contain investigation records.



\---



\## 4. R008 — Repeat Incident Pattern



\### Method



R008 uses the actual operational fields:



\- entity

\- asset

\- category

\- timestamp

\- case association



Only alerts associated with investigated cases are considered.



\### Prototype configuration



\- Recurrence window: 10 days

\- Minimum incidents: 4



These values are prototype/calibration values for the current synthetic dataset.



\### Metro Telecom validation



\- Expected cases: 4

\- Predicted cases: 4

\- True Positives: 4

\- False Positives: 0

\- False Negatives: 0

\- Precision: 1.0000

\- Recall: 1.0000

\- F1 Score: 1.0000



The detector correctly identified the repeated BRUTE\_FORCE pattern involving the same asset.



\---



\## 5. R009 — Combined Suspicious Investigation Behaviour



R009 combines evidence from different behavioural detectors.



Current configuration:



\- Minimum different behavioural rules: 2



R009 does not create an opaque combined score.



Instead, it preserves the evidence and explanations from the underlying rules.



\### Observed overlap



R006 and R007 overlap on:



\- Case: E004-C0019



Therefore R009 produces a combined behavioural finding for this case with:



\- R006 evidence

\- R007 evidence



There is no independent R009 ground-truth label in the current dataset, so independent Precision, Recall and F1 metrics are not reported for R009.



\---



\## 6. Explainability



Behavioural findings contain:



\- Rule ID

\- Problem type

\- Case/investigation identifiers where applicable

\- Supporting evidence

\- Human-readable reason

\- Relevant scores or measurements



The output is intended to remain understandable to a supervisor or risk/explanation layer.



\---



\## 7. Entity Isolation



Behavioural analysis is performed within the relevant entity.



This prevents records from other organisations from affecting:



\- R006 similarity analysis

\- R007 duration baselines

\- R008 recurrence detection



This is important because the database contains multiple organisations.



\---



\## 8. Ground Truth Usage



ground\_truth.csv is used only for post-detection evaluation.



It is NOT used as an input signal by the behavioural detectors.



Validation follows:



Operational data

&#x20;       ↓

Behaviour detectors

&#x20;       ↓

Predicted findings

&#x20;       ↓

Compare with ground\_truth.csv

&#x20;       ↓

TP / FP / FN

&#x20;       ↓

Precision / Recall / F1



\---



\## 9. Edge-Case Testing



The file:



test\_behaviour\_edge\_cases.py



was created to verify safe handling of the required edge cases.



All 7 tests passed:



1\. Missing/empty investigation notes

2\. Highly similar investigation notes

3\. Clearly different investigation notes

4\. Missing timestamps

5\. Negative investigation duration

6\. Repeated incident pattern

7\. Single isolated incident



No crashes or unsafe handling were observed in these tests.



\---



\## 10. API Integration



Behavioural findings are integrated into:



GET /cases/{case\_id}



The API returns behavioural findings together with the existing case information.



Finding information includes:



\- rule\_id

\- problem\_type

\- severity

\- reason

\- evidence



Example behavioural rules exposed through the API:



\- R006 — REPETITIVE\_INVESTIGATION

\- R007 — INVESTIGATION\_DURATION\_ANOMALY

\- R008 — REPEAT\_INCIDENT\_PATTERN

\- R009 — COMBINED\_SUSPICIOUS\_INVESTIGATION\_BEHAVIOUR



\---



\## 11. Existing Rule Engine



The existing R001-R004 rule engine was not modified.



The original rule engine was tested after behavioural integration and continues to execute successfully.



Existing rules:



\- R001 — Missing Investigation

\- R002 — Missing Evidence

\- R003 — Missing Escalation

\- R004 — Fast Critical Closure



\---



\## 12. Calibration Note



The thresholds used by the behavioural detectors are prototype/calibration values based on the current synthetic Metro Telecom dataset.



They should not be treated as universal industry thresholds.



Future calibration can use larger operational datasets and domain-specific baselines.



\---



\## 13. Validation Summary



\### R006



Precision: 1.0000  

Recall: 1.0000  

F1: 1.0000



\### R007



Precision: 1.0000  

Recall: 1.0000  

F1: 1.0000



\### R008



Precision: 1.0000  

Recall: 1.0000  

F1: 1.0000



\### R009



No independent ground-truth metric available.



Validated through overlap of R006 and R007 findings.



\---



\## 14. Files Added / Updated



Behaviour analytics implementation:



backend/services/behaviour\_analytics.py



Behaviour finding API integration:



backend/services/behaviour\_finding\_service.py



Edge-case tests:



backend/test\_behaviour\_edge\_cases.py



Ground-truth validation scripts:



backend/validate\_behaviour\_ground\_truth.py

backend/validate\_r007\_ground\_truth.py

backend/validate\_r008\_ground\_truth.py



Handoff document:



BEHAVIOUR\_ANALYTICS\_HANDOFF.md



\---



\## 15. Git Handoff



Current development branch:



metro\_telecom



The behavioural analytics work has been tested and integrated with the existing backend.



The branch should be pushed to the remote repository after committing the final validation and handoff files.



\---



\## 16. Handoff Target



The behavioural analytics module is intended to provide explainable findings to the ShadowWatch risk/explanation layer and supervisor dashboard.



The main behavioural outputs are:



R006 → repetitive investigation behaviour



R007 → investigation duration anomaly



R008 → repeat incident pattern



R009 → combined suspicious investigation behaviour

