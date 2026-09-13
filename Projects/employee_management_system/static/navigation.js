const menuButton = document.querySelector(
    "[data-navigation-toggle]",
);
const closeButton = document.querySelector(
    "[data-navigation-close]",
);
const backdropButton = document.querySelector(
    "[data-navigation-backdrop]",
);
const navigation = document.querySelector(
    "#primary-navigation",
);
const mobileNavigationQuery = window.matchMedia(
    "(max-width: 760px)",
);
let navigationWasOpenedBy = null;

function focusableNavigationItems() {
    if (!navigation) {
        return [];
    }

    return Array.from(
        navigation.querySelectorAll(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
    );
}

function synchronizeNavigationAvailability(isOpen) {
    if (!navigation) {
        return;
    }

    const isUnavailable = mobileNavigationQuery.matches && !isOpen;
    navigation.inert = isUnavailable;

    if (isUnavailable) {
        navigation.setAttribute("aria-hidden", "true");
    } else {
        navigation.removeAttribute("aria-hidden");
    }
}

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

    synchronizeNavigationAvailability(isOpen);

    if (isOpen) {
        navigationWasOpenedBy = document.activeElement;
        closeButton?.focus();
    } else if (
        navigationWasOpenedBy
        && document.contains(navigationWasOpenedBy)
    ) {
        navigationWasOpenedBy.focus();
        navigationWasOpenedBy = null;
    }
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
    });

    backdropButton?.addEventListener("click", () => {
        setNavigationOpen(false);
    });

    navigation.querySelectorAll("a[href]").forEach((link) => {
        link.addEventListener("click", () => {
            if (mobileNavigationQuery.matches) {
                setNavigationOpen(false);
            }
        });
    });

    document.addEventListener("keydown", (event) => {
        const isOpen = (
            menuButton.getAttribute("aria-expanded") === "true"
        );

        if (event.key === "Escape" && isOpen) {
            setNavigationOpen(false);
            return;
        }

        if (event.key !== "Tab" || !isOpen) {
            return;
        }

        const items = focusableNavigationItems();
        const firstItem = items[0];
        const lastItem = items[items.length - 1];

        if (event.shiftKey && document.activeElement === firstItem) {
            event.preventDefault();
            lastItem?.focus();
        } else if (
            !event.shiftKey
            && document.activeElement === lastItem
        ) {
            event.preventDefault();
            firstItem?.focus();
        }
    });

    mobileNavigationQuery.addEventListener("change", () => {
        setNavigationOpen(false);
    });

    synchronizeNavigationAvailability(false);
}

const localDateTimeFormatter = new Intl.DateTimeFormat(
    undefined,
    {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
        timeZoneName: "short",
    },
);

document.querySelectorAll("time[data-local-datetime]").forEach(
    (timeElement) => {
        const storedTimestamp = timeElement.dateTime;
        const localDate = new Date(storedTimestamp);

        if (Number.isNaN(localDate.getTime())) {
            return;
        }

        timeElement.textContent = localDateTimeFormatter.format(
            localDate,
        );
        timeElement.title = `Stored in UTC as ${storedTimestamp}`;
    },
);
