## 2024-05-18 - Home Assistant Config Flow Form Fields Helper Text
**Learning:** Home Assistant supports providing inline helper text directly beneath the configuration and options flow form fields using the `data_description` object within `strings.json` and `translations/*.json`.
**Action:** Use this to provide better descriptions of the fields rather than putting the explanation in the description box on top.
## 2024-03-24 - Helper text in Config Flows
**Learning:** Home Assistant configuration flows support inline field helper text by adding a `data_description` object containing keys that map to the `data` schema keys within `strings.json` and translation files.
**Action:** Use `data_description` rather than relying solely on the step `description` to provide specific, field-level guidance in Home Assistant integrations.
