from email_rules.core.type_defs import EmailTag
from email_rules.exporting._templates import _JinjaTemplate


class ActionTag(_JinjaTemplate):
    tag_name: EmailTag


class Templates:
    ACTION_TAG = ActionTag
