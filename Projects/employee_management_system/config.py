MONTHS_PER_YEAR = 12
TAX_RATE = 0.05
DEFAULT_ALLOWANCE = 5000
DEFAULT_OVERTIME = 3000

# Business schedule times use this local zone. Claimed occurrence timestamps
# are converted to UTC before they are stored.
WORKFLOW_TIME_ZONE = "Asia/Shanghai"

PRIMARY_STORAGE = "sqlite"
SUPPORTED_STORAGE_TYPES = {
    "json",
    "sqlite",
}
