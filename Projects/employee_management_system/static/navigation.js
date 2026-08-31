const menuButton = document.querySelector(
    "[data-navigation-toggle]",
);
const closeButton = document.querySelector(
    "[data-navigation-close]",
);
const navigation = document.querySelector(
    "#primary-navigation",
);

function setNavigationOpen(isOpen) {
    if (!menuButton || !navigation) {
        return;
    }

    navigation.classList.toggle("is-open", isOpen);
    document.body.classList.toggle(
        "navigation-open",
        isOpen,
    );
    menuButton.setAttribute(
        "aria-expanded",
        String(isOpen),
    );
    menuButton.setAttribute(
        "aria-label",
        isOpen
            ? "Close navigation"
            : "Open navigation",
    );
}

if (menuButton && navigation) {
    menuButton.addEventListener("click", () => {
        const isOpen = (
            menuButton.getAttribute("aria-expanded")
            === "true"
        );

        setNavigationOpen(!isOpen);
    });

    closeButton?.addEventListener("click", () => {
        setNavigationOpen(false);
        menuButton.focus();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setNavigationOpen(false);
            menuButton.focus();
        }
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 760) {
            setNavigationOpen(false);
        }
    });
}