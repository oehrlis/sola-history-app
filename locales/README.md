# Locales / Translation Files

This directory contains translation files for the SOLA History application's internationalization (i18n) support.

## Structure

- `en.json` - English translations (default language)
- `de.json` - German translations (Deutsch)

## Format

Each file is a JSON object with key-value pairs:

```json
{
  "key_name": "Translated text",
  "another_key": "Another translation"
}
```

## Usage

Translations are automatically loaded by the application at startup. The `t()` function in `app.py` handles translation lookups.

Example in code:
```python
st.title(t("app_title"))
st.button(t("admin_save_button"))
```

## Adding a New Language

1. Create a new JSON file (e.g., `fr.json` for French)
2. Copy the structure from `en.json`
3. Translate all values to the target language
4. Add the language code to `SUPPORTED_LANGS` in `app.py`
5. Update language selector format function if needed

## Translation Keys Organization

Keys are organized by functional area:

- **Application**: `app_*`, `page_*`, `language_*`
- **Authentication**: `password_*`
- **Tabs**: `tab_*`
- **Sidebar/Filters**: `sidebar_*`, `filter_*`, `option_*`
- **Errors**: `error_*`
- **Info Messages**: `info_*`
- **Year Tab**: `year_*`, `metric_*`, `chart_*`, `results_*`
- **Runner Tab**: `runner_*`, `select_*`
- **Overview Tab**: `overview_*`
- **Highlights Tab**: `highlights_*`
- **Planning Tab**: `planning_*`, `checklist_*`
- **Admin Tab**: `admin_*`, `please_*`
- **Common**: `download_*`

## Best Practices

1. **Keep keys consistent** across all language files
2. **Use descriptive key names** that indicate the context
3. **Preserve special formatting** (e.g., `**bold**`, `### headers`)
4. **Test translations** in the UI after changes
5. **Maintain alphabetical order** within sections (optional but helpful)
6. **Use UTF-8 encoding** for all files
7. **Escape special characters** properly in JSON strings

## Validation

To validate JSON syntax:
```bash
python -m json.tool locales/en.json > /dev/null
python -m json.tool locales/de.json > /dev/null
```

## Contributing

When adding new UI strings:

1. Add the English version to `en.json`
2. Add corresponding translations to all other language files
3. Use the `t()` function in the code
4. Test with both languages

## Fallback Behavior

If a translation key is missing:
1. Falls back to English (`en.json`)
2. Falls back to hardcoded critical strings in `app.py`
3. Returns the key name itself as last resort

This ensures the application remains functional even with incomplete translations.
