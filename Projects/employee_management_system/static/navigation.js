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
