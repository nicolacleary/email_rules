from email_rules.core.type_defs import EmailState, EmailTag
from email_rules.rules.basic_actions import RuleActionAddTag


def test_rule_action_add_tag() -> None:
    text = "some_tag"
    rule_action = RuleActionAddTag(
        tag_to_apply=EmailTag(text),
    )
    assert rule_action.apply(EmailState.create_initial_state()).tags == {
        EmailTag(text),
    }
