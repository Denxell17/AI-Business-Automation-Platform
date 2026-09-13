import re
import unittest
from pathlib import Path
from xml.etree import ElementTree


PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]
STATIC_DIRECTORY = PROJECT_DIRECTORY / "static"
TEMPLATE_DIRECTORY = PROJECT_DIRECTORY / "templates"


def relative_luminance(hex_color):
    channels = [
        int(hex_color[index:index + 2], 16) / 255
        for index in (1, 3, 5)
    ]
    linear_channels = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return (
        0.2126 * linear_channels[0]
        + 0.7152 * linear_channels[1]
        + 0.0722 * linear_channels[2]
    )


def contrast_ratio(first_color, second_color):
    lighter, darker = sorted(
        (
            relative_luminance(first_color),
            relative_luminance(second_color),
        ),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


class TestUiFoundations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stylesheet = (
            STATIC_DIRECTORY / "styles.css"
        ).read_text(encoding="utf-8")

    def test_approved_dark_and_light_tokens_are_defined(self):
        expected_tokens = {
            "--color-background: #1b1f24",
            "--color-surface: #242a31",
            "--color-text: #f4f6f8",
            "--color-link: #60a5fa",
            "--color-action: #2563eb",
            "--color-focus: #75b5ff",
            "--color-running: #60a5fa",
            "--color-disabled: #a8b3c0",
            ':root[data-theme="light"]',
        }

        for token in expected_tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.stylesheet)

    def test_core_color_pairs_meet_accessibility_contrast(self):
        text_pairs = (
            ("#f4f6f8", "#242a31"),
            ("#c1c9d2", "#242a31"),
            ("#60a5fa", "#242a31"),
            ("#f8fafc", "#2563eb"),
            ("#172033", "#ffffff"),
            ("#526173", "#ffffff"),
            ("#1d4ed8", "#ffffff"),
        )
        non_text_pairs = (
            ("#75b5ff", "#1b1f24"),
            ("#64748b", "#242a31"),
            ("#1d4ed8", "#f6f8fb"),
            ("#64748b", "#ffffff"),
        )

        for foreground, background in text_pairs:
            with self.subTest(
                foreground=foreground,
                background=background,
            ):
                self.assertGreaterEqual(
                    contrast_ratio(foreground, background),
                    4.5,
                )

        for foreground, background in non_text_pairs:
            with self.subTest(
                foreground=foreground,
                background=background,
            ):
                self.assertGreaterEqual(
                    contrast_ratio(foreground, background),
                    3,
                )

    def test_reusable_components_use_semantic_status_classes(self):
        for class_name in (
            ".ui-button--primary",
            ".ui-status--completed",
            ".ui-status--running",
            ".ui-status--failed",
            ".ui-status--disabled",
            ".ui-alert--danger",
            ".ui-empty-state",
            ".ui-table-wrapper",
        ):
            with self.subTest(class_name=class_name):
                self.assertIn(class_name, self.stylesheet)

        running_rule = re.search(
            r"\.ui-status--running\s*\{(?P<body>.*?)\}",
            self.stylesheet,
            re.DOTALL,
        )
        self.assertIsNotNone(running_rule)
        self.assertIn("var(--color-running)", running_rule.group("body"))

    def test_icon_sprite_contains_the_required_local_symbols(self):
        icon_tree = ElementTree.parse(STATIC_DIRECTORY / "icons.svg")
        symbol_ids = {
            symbol.attrib["id"]
            for symbol in icon_tree.findall(
                ".//{http://www.w3.org/2000/svg}symbol"
            )
        }
        required_symbols = {
            "icon-dashboard",
            "icon-employees",
            "icon-workflows",
            "icon-agent",
            "icon-assistant",
            "icon-report",
            "icon-activity-log",
            "icon-users",
            "icon-health",
            "icon-docs",
            "icon-check",
            "icon-running",
            "icon-x",
            "icon-minus",
            "icon-sign-out",
        }

        self.assertTrue(required_symbols.issubset(symbol_ids))
        self.assertEqual(len(symbol_ids), 19)

    def test_brand_assets_are_valid_accessible_svg_files(self):
        brand_directory = STATIC_DIRECTORY / "brand"
        expected_assets = (
            "abap-icon.svg",
            "abap-lockup.svg",
            "abap-wordmark.svg",
            "abap-wordmark-monochrome.svg",
            "abap-wordmark-reversed.svg",
        )

        for asset_name in expected_assets:
            with self.subTest(asset_name=asset_name):
                root = ElementTree.parse(
                    brand_directory / asset_name
                ).getroot()
                self.assertEqual(
                    root.tag,
                    "{http://www.w3.org/2000/svg}svg",
                )
                self.assertEqual(root.attrib.get("role"), "img")
                self.assertTrue(
                    root.attrib.get("aria-labelledby")
                    or root.attrib.get("aria-label")
                )

    def test_jinja_macros_preserve_visible_status_text(self):
        macros = (
            PROJECT_DIRECTORY / "templates" / "ui_macros.html"
        ).read_text(encoding="utf-8")

        self.assertIn('macro icon(name, label=none', macros)
        self.assertIn('aria-hidden="true"', macros)
        self.assertIn('class="ui-status ui-status--{{ normalized }}"', macros)
        self.assertIn("<span>{{ value }}</span>", macros)

    def test_application_shell_supports_keyboard_navigation(self):
        application_base = (
            TEMPLATE_DIRECTORY / "application_base.html"
        ).read_text(encoding="utf-8")
        base = (TEMPLATE_DIRECTORY / "base.html").read_text(
            encoding="utf-8"
        )
        navigation = (STATIC_DIRECTORY / "navigation.js").read_text(
            encoding="utf-8"
        )

        self.assertIn('class="skip-link" href="#main-content"', base)
        self.assertIn('id="main-content"', application_base)
        self.assertIn('aria-controls="primary-navigation"', application_base)
        self.assertIn('aria-expanded="false"', application_base)
        self.assertIn("navigation.inert = isUnavailable", navigation)
        self.assertIn('event.key === "Escape"', navigation)

    def test_responsive_and_reduced_motion_rules_are_present(self):
        self.assertIn("@media (max-width: 760px)", self.stylesheet)
        self.assertIn("@media (max-width: 640px)", self.stylesheet)
        self.assertIn("@media (max-width: 380px)", self.stylesheet)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.stylesheet)

    def test_scrollable_data_tables_have_accessible_regions(self):
        expected_regions = {
            "home.html": "Recent workflow executions",
            "employees.html": "Scrollable employee directory",
            "workflows.html": "Scrollable workflow directory",
            "user_accounts.html": "Scrollable user account directory",
            "workforce_report.html": "Scrollable department headcount table",
            "agent_execution_history.html": "Agent Execution history",
        }

        for template_name, accessible_name in expected_regions.items():
            with self.subTest(template=template_name):
                template = (TEMPLATE_DIRECTORY / template_name).read_text(
                    encoding="utf-8"
                )
                self.assertIn('role="region"', template)
                self.assertIn('tabindex="0"', template)
                self.assertIn(accessible_name, template)

    def test_tables_expose_captions_and_header_scopes(self):
        table_templates = (
            "home.html",
            "employees.html",
            "workflows.html",
            "user_accounts.html",
            "workforce_report.html",
            "agent_execution_history.html",
        )

        for template_name in table_templates:
            with self.subTest(template=template_name):
                template = (TEMPLATE_DIRECTORY / template_name).read_text(
                    encoding="utf-8"
                )
                self.assertIn("<caption", template)
                self.assertIn('scope="col"', template)

        agent_history = (
            TEMPLATE_DIRECTORY / "agent_execution_history.html"
        ).read_text(encoding="utf-8")
        self.assertNotIn('class="visually-hidden"', agent_history)
        self.assertIn('class="ui-visually-hidden"', agent_history)

    def test_headcount_bars_use_semantic_progress_elements(self):
        for template_name, class_name in (
            ("home.html", "department-bar"),
            ("workforce_report.html", "report-bar"),
        ):
            with self.subTest(template=template_name):
                template = (TEMPLATE_DIRECTORY / template_name).read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    f'<progress class="{class_name}"',
                    template,
                )
                self.assertIn("aria-label=", template)
                self.assertNotIn("style=", template)


if __name__ == "__main__":
    unittest.main()
