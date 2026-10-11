import {Component} from "@odoo/owl";
import {SelectCreateDialog} from "@web/views/view_dialogs/select_create_dialog";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardWidgetProps} from "@web/views/widgets/standard_widget_props";
import {useService} from "@web/core/utils/hooks";

/**
 * Open the catalogue texts that can still be added to a document in a
 * multi-select dialog, then add the selected ones as catalogue lines.
 *
 * @param {Object} services orm and dialog services
 * @param {Object} params
 * @param {String} params.resModel model of the document
 * @param {Number} params.resId id of the saved document
 * @param {Function} params.onAdded called once the texts are added
 */
export async function openTextElementCatalogue({orm, dialog}, params) {
    const {resModel, resId, onAdded} = params;
    const domain = await orm.call(resModel, "get_text_element_catalogue_domain", [
        [resId],
    ]);
    dialog.add(SelectCreateDialog, {
        resModel: "text.element",
        domain,
        title: _t("Add from catalogue"),
        noCreate: true,
        multiSelect: true,
        onSelected: async (elementIds) => {
            await orm.call(resModel, "action_add_text_elements", [[resId], elementIds]);
            await onAdded();
        },
    });
}

/**
 * Button of the Text Elements tab of a document.
 */
export class AddTextElementFromCatalogue extends Component {
    static template = "text_element_base.AddTextElementFromCatalogue";
    static props = {...standardWidgetProps};

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
    }

    async onClick() {
        const record = this.props.record;
        if (record.isNew || record.dirty) {
            const saved = await record.save();
            if (!saved) {
                return;
            }
        }
        await openTextElementCatalogue(
            {orm: this.orm, dialog: this.dialog},
            {
                resModel: record.resModel,
                resId: record.resId,
                onAdded: () => record.load(),
            }
        );
    }
}

registry.category("view_widgets").add("text_element_add_from_catalogue", {
    component: AddTextElementFromCatalogue,
});

/**
 * Client action returned by action_add_element_wizard, the former button
 * that views of client modules still call.
 */
registry
    .category("actions")
    .add("text_element_add_from_catalogue", async (env, action) => {
        const {res_model, res_id} = action.params;
        await openTextElementCatalogue(env.services, {
            resModel: res_model,
            resId: res_id,
            onAdded: () =>
                env.services.action.doAction({
                    type: "ir.actions.client",
                    tag: "soft_reload",
                }),
        });
    });
