from . import models


def _enable_text_element_on_purchase(env):
    env["ir.model"].search([("model", "=", "purchase.order")]).write(
        {"can_be_used_with_text_elements": True}
    )
