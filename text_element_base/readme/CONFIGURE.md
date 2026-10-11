Members of **Text Elements Manager** (granted to Settings administrators)
maintain the catalogue in **Text Elements → Configuration → Text Elements**.
Other internal users can read it and adapt texts on their own documents.

A text element answers three questions:

* **What** — its name (internal, not printed) and its content. In the editor,
  type `/` and choose *Dynamic Placeholder* to insert a value of the document,
  such as the customer name. The former `[[partner_id.name]]` syntax keeps
  working. A placeholder that does not match a field is refused when saving.
* **Where** — the document type (empty: every document), the position (top of
  document, before lines, after totals, bottom of document), its order among
  the texts of the same position, and optional page breaks.
* **When** — whether it is added automatically to new documents, a condition
  on the document, a validity period, and the company.

The **Preview** tab renders the text on a sample document and tells whether
it would be printed.
