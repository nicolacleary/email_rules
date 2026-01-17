# Email Rules

## Rendering

### Custom Rule Filters

```
class EnvironmentMatchesSpamThreshold(RuleFilter):
    def evaluate(self, email: Email) -> bool:
        return False  # TODO: implement


class SpamTestFilter(RuleFilter):
    def evaluate(self, email: Email) -> bool:
        return False  # TODO: implement


class CustomSieveRenderer(SieveRenderer):
    def render_rule_filter(self, rule_filter: RuleFilter) -> RenderedRuleFilter:
        if type(rule_filter) is EnvironmentMatchesSpamThreshold:
            return RenderedRuleFilter('environment :matches "vnd.proton.spam-threshold" "*"')

        if type(rule_filter) is SpamTestFilter:
            return RenderedRuleFilter('spamtest :value "ge" :comparator "i;ascii-numeric" "${1}"')

        return super().render_rule_filter(rule_filter)
```
