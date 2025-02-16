from . import models


def _enable_text_element_on_sale(env):
    env["ir.model"].search([("model", "=", "sale.order")]).write(
        {"can_be_used_with_text_elements": True}
    )
