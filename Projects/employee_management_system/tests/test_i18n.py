import re
import unittest
from types import SimpleNamespace

from babel.messages.pofile import read_po

from i18n import (
    TRANSLATIONS_DIRECTORY,
    browser_message_label,
    request_i18n_context,
    resolve_interface_language,
    translation_for,
    validated_language,
)


PLACEHOLDER_PATTERN = re.compile(r"%\([^)]+\)[a-zA-Z]")


class TestInternationalization(unittest.TestCase):
    def test_language_codes_are_validated_exactly(self):
        self.assertEqual(validated_language("en"), "en")
        self.assertEqual(validated_language("ja"), "ja")
        self.assertIsNone(validated_language("en-US"))
        self.assertIsNone(validated_language("JA"))
        self.assertIsNone(validated_language(None))

    def test_resolution_uses_session_then_account_then_english(self):
        self.assertEqual(resolve_interface_language("ja", "en"), "ja")
        self.assertEqual(resolve_interface_language(None, "ja"), "ja")
        self.assertEqual(resolve_interface_language("invalid", None), "en")

    def test_request_context_is_scoped_and_sets_direction_metadata(self):
        request = SimpleNamespace(
            session={"interface_language": "ja"},
            state=SimpleNamespace(authenticated_user=None),
        )
        context = request_i18n_context(request)

        self.assertEqual(context["interface_language"], "ja")
        self.assertEqual(context["text_direction"], "ltr")
        self.assertEqual(context["_"]("Dashboard"), "ダッシュボード")

    def test_unknown_and_business_text_is_never_translated(self):
        translator = translation_for("ja").gettext
        business_value = "Northwind Customer Alpha"

        self.assertEqual(translator(business_value), business_value)
        self.assertEqual(
            browser_message_label(business_value, translator),
            business_value,
        )

    def test_english_source_is_the_fallback(self):
        self.assertEqual(translation_for("en").gettext("Dashboard"), "Dashboard")
        self.assertEqual(
            translation_for("ja").gettext("Uncatalogued future message"),
            "Uncatalogued future message",
        )

    def test_japanese_catalog_is_complete_and_preserves_placeholders(self):
        catalog_path = (
            TRANSLATIONS_DIRECTORY / "ja" / "LC_MESSAGES" / "messages.po"
        )
        with catalog_path.open(encoding="utf-8") as catalog_file:
            catalog = read_po(catalog_file, locale="ja")

        messages = [message for message in catalog if message.id]
        self.assertGreater(len(messages), 600)
        for message in messages:
            self.assertNotIn("fuzzy", message.flags)
            source_ids = message.id if isinstance(message.id, tuple) else (message.id,)
            translations = (
                message.string
                if isinstance(message.string, tuple)
                else (message.string,)
            )
            self.assertTrue(all(translations))
            source_placeholders = set().union(
                *(set(PLACEHOLDER_PATTERN.findall(value)) for value in source_ids)
            )
            for translated in translations:
                self.assertEqual(
                    set(PLACEHOLDER_PATTERN.findall(translated)),
                    source_placeholders,
                )


if __name__ == "__main__":
    unittest.main()
