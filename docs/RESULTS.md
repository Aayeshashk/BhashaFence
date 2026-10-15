

\# BhashaFence — Evaluation Results



\## 1. Overview



BhashaFence is a synthetic AI-agent security evaluation lab. It compares a baseline executor with a policy-enforced executor and includes multilingual structured-action evaluation and an indirect-prompt-injection integration pilot.



The current results describe the behavior of the synthetic evaluation system. They do not prove that a real AI model can resist multilingual prompt injection.



\## 2. Baseline vs. Policy Defense



The comparison evaluated nine synthetic scenarios under each configuration.



| Metric | Baseline | Policy Defense |

|---|---:|---:|

| Total calls | 9 | 9 |

| Successful calls | 6 | 4 |

| Blocked calls | 3 | 5 |

| Executed synthetic actions | 6 | 4 |

| Legitimate tasks succeeded | 4/4 | 4/4 |

| Eligible untrusted sensitive requests denied | 0/2 | 2/2 |

| Untrusted sensitive actions executed | 2 | 0 |

| Legitimate-task success rate | 100% | 100% |

| Authorization denial rate | 0% | 100% |



\### Interpretation



The baseline executor allowed two eligible sensitive actions originating from untrusted content. The policy-enforced executor blocked both.



Both configurations successfully completed the four tasks labelled legitimate in this fixed scenario set.



These results demonstrate the behavior of the implemented synthetic policy. They are not evidence of real-world attack prevention.



\## 3. Multilingual Evaluation



The multilingual structured-action evaluation completed successfully for four language categories:



\- English (`en`)

\- Hindi (`hi`)

\- Marathi (`mr`)

\- Code-mixed (`code\_mixed`)



The generated report shows a 100% legitimate-task success rate for each language category in both configurations. The baseline reports a 0% authorization denial rate, while the defense reports 100%.



\*\*Important limitation:\*\* The harness supplies structured tool calls. This evaluation does not test whether a model understands the language or detects prompt injection in natural-language text.



Detailed reports:



\- `artifacts/multilingual\_evaluation.json`

\- `artifacts/multilingual\_evaluation.csv`



\## 4. Indirect-Injection Integration Pilot



The pilot dataset contains 16 draft records across four scenarios and four language categories.



The structural audit passed. The deterministic integration runner completed with:



\- 16 records validated.

\- 32 paired evaluation attempts.

\- 16 baseline attempts and 16 defense attempts.

\- Eight attempts per language category across both conditions.

\- No real model calls.

\- Tool execution disabled.

\- JSON and CSV reports successfully exported.



Reports:



\- `artifacts/indirect\_injection/pilot\_quality\_audit.json`

\- `artifacts/indirect\_injection/integration\_run/pilot\_integration.json`

\- `artifacts/indirect\_injection/integration\_run/pilot\_integration.csv`



The integration runner uses a deterministic test double. It validates the evaluation pipeline, not actual model security.



The pilot records remain drafts and require independent linguistic review.



\## 5. Automated Testing



The full test suite passed:



```text

124 passed

```



The indirect-injection structural audit also passed.



These checks validate the existing tests and dataset structure. They do not guarantee that the system has no defects.



\## 6. Limitations



1\. All tool effects are synthetic; no real external actions are performed.

2\. Source labels are supplied by the harness or dataset.

3\. The multilingual evaluation does not measure natural-language understanding.

4\. The indirect-injection pilot does not call a real model.

5\. The pilot translations have not completed independent linguistic review.

6\. The dataset is small and does not provide statistical evidence of security.

7\. A reported task completion value is not proof that a real task was completed.



\## 7. Future Work



\- Obtain independent linguistic review of Hindi, Marathi, and code-mixed scenarios.

\- Integrate real models through controlled evaluation adapters.

\- Test model-generated proposals separately from harness-supplied structured actions.

\- Expand the dataset with additional attack and legitimate-task scenarios.

\- Report sample counts and metric denominators alongside all results.

\- Repeat experiments across additional models and datasets.



\## 8. Conclusion



BhashaFence demonstrates a working synthetic authorization-policy comparison, multilingual structured-action reporting, and indirect-injection evaluation pipeline.



In the fixed comparison scenarios, the policy defense blocked all eligible untrusted sensitive actions while preserving success on the four designated legitimate tasks.



The current evidence supports a limited conclusion about the synthetic policy and evaluation harness. Real-model experiments and independently reviewed multilingual data are required before making broader claims about prompt-injection resistance.



