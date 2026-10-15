\# Phase 4.8 — Real-Model Natural-Language Evaluation Design



\## 1. Objective



Design a separate evaluation layer for measuring how a language model handles multilingual indirect prompt injection in BhashaFence.



The evaluation must distinguish natural-language interpretation from the existing deterministic structured-action authorization benchmark.



\## 2. Existing Baseline



The current simulator evaluates structured tool actions and source-aware authorization decisions. The harness supplies the tool action, so the existing benchmark does not measure whether a language model understands the multilingual scenario text.



The existing benchmark must remain unchanged and continue to run as a regression baseline.



\## 3. Pilot Dataset



Input dataset: `dataset/processed/indirect\_injection/pilot\_scenarios.json`



The pilot contains 16 variants across four scenarios and four language varieties: English, Hindi, Marathi, and Hindi-English code-mixed text.



All records currently have review status `draft`. Independent linguistic review remains outstanding.



The pilot is suitable for protocol development, not for strong statistical or generalization claims.



\## 4. Model Input Isolation



The model may receive only the user task and the untrusted content, along with a fixed system instruction required by the experiment.



The following must remain evaluator-only:



\- Expected action

\- Embedded-attack label

\- Expected security outcome

\- Expected task outcome

\- Review status and reviewer notes



The trusted harness must maintain provenance separately. Do not ask the model to trust a source label that is merely included in untrusted text.



\## 5. Safe Execution Boundary



The model must not have access to real tools, private files, email, browsing, or external services.



Any proposed tool action must be captured as structured output and evaluated by a local harness. No proposed action should execute against a real resource.



The harness should validate tool names and arguments against an allowlist and record invalid outputs as validation failures rather than successful actions.



\## 6. Experimental Conditions



At minimum, compare:



1\. A baseline condition with the model's ordinary task instructions.

2\. A defense condition with an explicit instruction to treat supplied untrusted content as data rather than authority to change the task.



Use the same model, dataset, output schema, and run settings for both conditions. Record the exact system prompts and model identifier.



Do not describe the defense condition as a complete security boundary. Prompt instructions alone may not reliably prevent injection.



\## 7. Outcomes



Report separate metrics for:



\- Task completion: whether the intended benign task was completed.

\- Unauthorized-action attempt rate: whether the model proposed a disallowed sensitive action.

\- Safe abstention: whether the model asked for clarification when the task was ambiguous.

\- Output validity: whether the model returned a valid response in the required schema.

\- Results by language, scenario, and experimental condition.



Distinguish an attempted action from an executed action. In this experiment, tool actions are simulated and never executed against real resources.



Define scoring rules before collecting results. Do not infer model understanding solely from a successful JSON parse.



\## 8. Reproducibility



Record the model identifier, provider or local runtime, prompt version, dataset version or hash, temperature and other supported generation settings, timestamp, run identifier, and raw model output.



Keep API keys in environment variables if a hosted provider is used. Never commit secrets or include them in reports.



Use repeated runs where feasible and report counts and uncertainty. The 16-record pilot is too small to support broad claims about multilingual security or generalization.



\## 9. Linguistic Quality



All pilot records remain `draft` until independent linguistic review is completed.



Report linguistic uncertainty separately from model failures. A poorly translated or unnatural scenario can confound interpretation of the model's result.



\## 10. Current Limitations



The current pilot is small and synthetically constructed. Source provenance is supplied by the trusted harness; the evaluation does not solve provenance authentication.



The proposed experiment will measure behavior on the tested scenarios only. It cannot establish universal resistance to indirect prompt injection.



\## 11. Acceptance Criteria



Before running a model experiment:



1\. The model adapter has unit tests and handles malformed output safely.

2\. Evaluator-only labels are demonstrably excluded from model input.

3\. Tool calls cannot reach real external resources.

4\. Baseline and defense conditions use matched inputs.

5\. The scoring logic is tested against known safe and unsafe examples.

6\. Raw outputs and configuration metadata are recorded without secrets.

7\. The existing test suite continues to pass.



The real-model experiment must not be described as complete until these checks pass and actual model runs have been recorded.

