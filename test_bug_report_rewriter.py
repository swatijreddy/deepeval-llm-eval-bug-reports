from deepeval.metrics import GEval
from deepeval.metrics import HallucinationMetric
from deepeval.metrics import PromptAlignmentMetric
from deepeval.metrics import JsonCorrectnessMetric
from deepeval.test_case import SingleTurnParams

from deepeval.models import AnthropicModel
from deepeval import assert_test
from bug_report_rewriter import BugReportSchema, build_test_case
from customer_issues_test_data import customer_issue_reports
import pytest

# Judge model — Claude Haiku, scoring every metric below
judge_model = AnthropicModel(model="claude-haiku-4-5-20251001", temperature=0)


# MODEL-BASED GRADING (custom criteria) — is the rewrite factually accurate?

@pytest.mark.parametrize("issue", customer_issue_reports)
def test_correctness(issue):
    test_case = build_test_case(issue)
    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine whether the actual output is factually correct based on input.",
        threshold=0.5,
        model=judge_model,
        evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT]
    )
    assert_test(test_case, [correctness_metric])


# MODEL-BASED GRADING (pre-built) — did the rewrite invent details not in the original report?
@pytest.mark.parametrize("issue", customer_issue_reports)
def test_hallucination(issue):
    test_case = build_test_case(issue)
    hallucination_metric = HallucinationMetric(
        threshold=0.5,
        model=judge_model
    )
    assert_test(test_case, [hallucination_metric])


# MODEL-BASED GRADING (pre-built) — were the explicit formatting instructions followed?
@pytest.mark.parametrize("issue", customer_issue_reports)
def test_prompt_alignment(issue):
    test_case = build_test_case(issue)
    prompt_alignment_metric = PromptAlignmentMetric(
        prompt_instructions=[
            "Output must be in JSON format",
            "Output must include exactly these keys: title, summary, steps_to_reproduce, expected, actual, severity, priority",
            "Any field that cannot be inferred from the input must say 'Not specified — needs clarification' instead of being guessed"],
        threshold=0.5,
        model=judge_model,
        include_reason=True
    )
    assert_test(test_case, [prompt_alignment_metric])


# MODEL-BASED GRADING (pre-built) — is the output valid JSON matching BugReportSchema?
@pytest.mark.parametrize("issue", customer_issue_reports)
def test_json_correctness(issue):
    test_case = build_test_case(issue)
    json_correctness_metric = JsonCorrectnessMetric(
        expected_schema=BugReportSchema,
        threshold=0.5,
        model=judge_model,
        include_reason=True,
        strict_mode=False
    )
    assert_test(test_case, [json_correctness_metric])

# NOTE: this metric gave inconsistent results while testing — sometimes it said
# the JSON was fine in its own explanation, but still marked the test as failed.
# Kept it anyway since it shows the check working; just double-check the
# "reason" text before trusting a FAILED result here.
