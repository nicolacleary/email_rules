# Modelling email filtering rules

Define filtering rules in Python with conditions:

```python
Rule(
    comment="Filter out emails asking for feedback, reviews, etc.",
    filter_expr=(
        RuleSubjectContains(
            text=EmailSubject("your feedback is important to us"),
        )
        | RuleSubjectContains(
            text=EmailSubject("Please tell us about your experience"),
        )
    ),
    actions=[
        RuleActionMoveToFolder(folder=Folders.FEEDBACK_ETC),
        RuleActionMarkAsRead(),
        RuleActionStopProcessingCurrentFile(),
    ]
)
```

Render to Sieve for use with mail servers that support it:

```
require ["fileinto", "imap4flags", "include"];

# Filter out emails asking for feedback, reviews, etc.
if anyof (header :contains "subject" "your feedback is important to us", header :contains "subject" "please tell us about your experience") {
    fileinto "feedback_etc";
    addflag "\\Seen";
    return;
}
```

Write unit tests to catch unintended behaviour changes:

```python
def test_feedback_emails_are_filtered_out() -> None:
    email = create_email(email_subject=EmailSubject("Your feedback is important to us"))
    with EmailRuleSimulation(inbox=EXAMPLE_1_ACCOUNT_SETTINGS, email=email) as email_final_state:
        email_final_state.assert_is_read()
        email_final_state.assert_is_moved_to(EXAMPLE_1_FOLDERS.FEEDBACK_ETC)

def test_other_emails_reach_the_inbox() -> None:
    email = create_email()
    with EmailRuleSimulation(inbox=EXAMPLE_1_ACCOUNT_SETTINGS, email=email) as email_final_state:
        email_final_state.assert_is_unread()
        email_final_state.assert_is_moved_to(INBOX)
```

For examples see `./examples`

```bash
make venv
. .venv/bin/activate

# To see the rendering
python examples/example_1.py

# To see the test output
pytest examples

```
