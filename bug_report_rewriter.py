
from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel
from customer_issues_test_data import customer_issue_reports
from deepeval.test_case import LLMTestCase

load_dotenv()
client = Anthropic()

MODEL = "claude-haiku-4-5-20251001"


# SYSTEM UNDER TEST — rewrites one vague customer report into a structured bug report
def rewrite_bug_report(issue_text):

    prompt = f"""You are a QA Engineer. You are given a customer issue report regarding a web application.
    Your task is to read the issue and rewrite it in a more clear and structured format.

    If any field cannot be reasonably inferred from the original report, write exactly:
    "Not specified — needs clarification" for that field. Do not guess or invent details.

    The bug report should consist of the following sections:
    1. title: A headline that summarizes the issue in one line.
    2. summary: A brief description of the issue.
    3. steps_to_reproduce: step by step instructions on how to reproduce the issue.
    4. expected: What the expected behavior is.
    5. actual: What the actual behavior is.
    6. severity: The severity of the issue (Critical, Major, Minor).
    7. priority: The priority of the issue (High, Medium, Low).

    Give the output with these exact keys: title, summary, steps_to_reproduce, expected, actual, severity, priority.
    steps_to_reproduce must always be a list of strings, even if only one step is known or if
    the value is the placeholder text — wrap it in a list, e.g. ["Not specified — needs clarification"].
    Give the output as raw JSON only — no markdown code fences, no extra text before or after the JSON object.
    
    Customer issue report:
    {issue_text}
    """
    message = client.messages.create(
        model = MODEL,
        max_tokens = 500,
        temperature = 0,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    return message.content[0].text.strip()


# The expected JSON structure for JsonCorrectnessMetric to check the output against
class BugReportSchema(BaseModel):
    title: str
    summary: str
    steps_to_reproduce: list[str]
    expected: str
    actual: str
    severity: str
    priority: str


# Runs rewrite_bug_report() once for each issue and stores the results,
# so we don't call the API again every time a metric needs the same output

def get_rewritten_reports():

    rewritten_bug_reports = {}
    for issue in customer_issue_reports:
        output = rewrite_bug_report(issue)
        rewritten_bug_reports[issue] = output
    return rewritten_bug_reports


rewritten_bug_reports = get_rewritten_reports()

def build_test_case(issue):
    return(LLMTestCase(
            input=issue,
            actual_output=rewritten_bug_reports[issue],
            context=[issue]))

