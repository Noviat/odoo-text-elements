from . import models


def _enable_text_element_on_aml(env):
    env["ir.model"].search([("model", "=", "account.move")]).write(
        {"can_be_used_with_text_elements": True}
    )
