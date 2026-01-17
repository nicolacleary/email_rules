from email_rules.core.type_defs import EmailState, EmailTag
from email_rules.rules.type_defs import RuleAction


class RuleActionAddTag(RuleAction):
    tag_to_apply: EmailTag

    def apply(self, email_state: EmailState) -> EmailState:
        email_state.tags.add(self.tag_to_apply)
        return email_state
