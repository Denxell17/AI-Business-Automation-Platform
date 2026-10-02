# ABAP Internationalization Architecture

## Status

The initial English and Japanese browser-interface localization milestone was
implemented on October 2, 2026. English source text is the fallback language.
The approved UI/UX remains the protected visual baseline.

## Runtime design

- Python gettext catalogs and Babel extraction/compilation provide translations.
- Jinja's i18n extension exposes request-scoped gettext functions to templates.
- Supported language codes are exact (`en`, `ja`); unsupported values are rejected.
- Resolution order is authenticated session, persisted account preference, then English.
- Anonymous preferences stay in the signed session. Authenticated changes are also
  stored on the user account. Login synchronizes the persisted preference into the
  new session, and logout preserves only the validated language preference.
- Plain browser error responses translate only explicitly allowlisted application
  messages. Arbitrary database, service, user, and business text is never used as a
  translation key.

## Separation of concerns

`interface_language` controls application chrome and fixed UI messages only. It
does not control currency, region, number/date policy, exported CSV headers, PDF
content, audit-log payloads, API/OpenAPI responses, or AI Assistant response
language. Region/currency and a future AI response-language preference require
separate fields and product decisions.

## Files and workflow

- Runtime helpers: `Projects/employee_management_system/i18n.py`
- Extraction configuration: `Projects/employee_management_system/babel.cfg`
- Source catalog: `Projects/employee_management_system/translations/messages.pot`
- Japanese catalog: `translations/ja/LC_MESSAGES/messages.po` and compiled
  `messages.mo`
- Account schema: SQLite additive initialization and PostgreSQL migration
  `009_add_user_interface_language.sql`

After changing fixed UI text, extract messages, update the locale catalog, compile
it, and run the i18n and full application test suites. Catalog tests require every
Japanese entry to be translated, non-fuzzy, and placeholder-compatible.

## Extension rules

Adding a language requires a supported locale entry, text direction metadata, a
complete catalog, and regression tests. Templates use logical/responsive layout
behavior and the root `dir` attribute is already request-driven, but full RTL
support still requires a dedicated design and browser review before enabling an
RTL locale.
