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
        const nextThemeLabel = nextTheme === "light"
            ? root.dataset.lightThemeLabel
            : root.dataset.darkThemeLabel;
        const useNextThemeLabel = nextTheme === "light"
            ? root.dataset.useLightThemeLabel
            : root.dataset.useDarkThemeLabel;

        document.querySelectorAll("[data-theme-toggle]").forEach(
            (button) => {
                button.setAttribute(
                    "aria-label",
                    useNextThemeLabel,
                );
                button.setAttribute(
                    "title",
                    useNextThemeLabel,
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
