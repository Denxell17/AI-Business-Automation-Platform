(() => {
    const storageKey = "abap-theme";
    const supportedThemes = new Set(["dark", "light"]);
    const root = document.documentElement;

    function storedTheme() {
        try {
            const value = window.localStorage.getItem(storageKey);
            return supportedThemes.has(value) ? value : null;
        } catch {
            return null;
        }
    }

    function preferredTheme() {
        const savedTheme = storedTheme();

        if (savedTheme) {
            return savedTheme;
        }

        return "dark";
    }

    function updateControls(theme) {
        const nextTheme = theme === "dark" ? "light" : "dark";
        const nextThemeLabel = (
            `${nextTheme[0].toUpperCase()}${nextTheme.slice(1)} theme`
        );

        document.querySelectorAll("[data-theme-toggle]").forEach(
            (button) => {
                button.setAttribute(
                    "aria-label",
                    `Use ${nextTheme} theme`,
                );
                button.setAttribute(
                    "title",
                    `Use ${nextTheme} theme`,
                );

                const label = button.querySelector(
                    "[data-theme-label]",
                );

                if (label) {
                    label.textContent = nextThemeLabel;
                }
            },
        );
    }

    function applyTheme(theme, persist = false) {
        root.dataset.theme = theme;
        root.style.colorScheme = theme;

        if (persist) {
            try {
                window.localStorage.setItem(storageKey, theme);
            } catch {
                // The theme still applies when storage is unavailable.
            }
        }

        updateControls(theme);
    }

    applyTheme(preferredTheme());

    document.addEventListener("DOMContentLoaded", () => {
        updateControls(root.dataset.theme || preferredTheme());

        document.querySelectorAll("[data-theme-toggle]").forEach(
            (button) => {
                button.addEventListener("click", () => {
                    const nextTheme = root.dataset.theme === "light"
                        ? "dark"
                        : "light";
                    applyTheme(nextTheme, true);
                });
            },
        );
    });
})();
