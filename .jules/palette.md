## 2024-03-24 - Helper text in Config Flows
**Learning:** Home Assistant configuration flows support inline field helper text by adding a `data_description` object containing keys that map to the `data` schema keys within `strings.json` and translation files.
**Action:** Use `data_description` rather than relying solely on the step `description` to provide specific, field-level guidance in Home Assistant integrations.
