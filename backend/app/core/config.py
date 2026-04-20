from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres
    postgres_user: str = "jobhunter"
    postgres_password: str = "changeme"
    postgres_db: str = "jobhunter"
    postgres_host: str = "db"
    postgres_port: int = 5432

    # Computed database URLs
    database_url: str = ""
    database_url_sync: str = ""

    # App
    log_level: str = "INFO"

    # Apify
    apify_api_token: str = ""
    # Comma-separated "keyword|location" pairs, e.g.:
    #   LINKEDIN_SEARCHES=Security Engineer|United States,Security Analyst|United States
    linkedin_searches: str = "security|United States,software engineer|United States"
    linkedin_pages_per_search: int = 3

    # Greenhouse boards (comma-separated board tokens)
    greenhouse_board_tokens: str = ""

    # Lever companies (comma-separated company slugs)
    lever_company_slugs: str = ""

    # Ashby companies (comma-separated company slugs)
    ashby_company_slugs: str = ""

    # Workday companies (comma-separated "tenant:board" or "tenant:board:wdhost" triples)
    # Examples: intel:External,dell:External,paypal:jobs,equinix:External
    workday_companies: str = ""

    # Workday CSRF companies (same format — for boards that require CSRF token)
    # Examples: nvidia:NVIDIAExternalCareerSite:wd5,salesforce:salesforce:wd12
    workday_csrf_companies: str = ""

    # Big tech company connectors
    # Search queries for each — comma-separated, empty disables the source
    google_search_queries: str = "software engineer new grad,software engineer entry level"
    amazon_search_queries: str = "software development engineer"
    apple_search_queries: str = "software engineer"
    microsoft_search_queries: str = "software engineer,new grad software engineer"
    meta_search_queries: str = "software engineer"

    # Set to "false" to disable individual big tech connectors
    google_enabled: str = "true"
    amazon_enabled: str = "true"
    apple_enabled: str = "true"
    microsoft_enabled: str = "true"
    meta_enabled: str = "true"

    # SmartRecruiters companies (comma-separated company identifiers)
    # Example: Visa,AnotherCo
    smartrecruiters_companies: str = ""

    # Jobright search queries (comma-separated)
    jobright_queries: str = ""
    # Max pages per Jobright query (16 jobs/page). 15 pages ≈ 240 jobs.
    jobright_max_pages: int = 15

    # Phase 2: Claude scoring
    anthropic_api_key: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    def model_post_init(self, __context: object) -> None:
        if not self.database_url:
            self.database_url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        if not self.database_url_sync:
            self.database_url_sync = (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )

    @property
    def greenhouse_token_list(self) -> list[str]:
        """Returns list of Greenhouse board tokens parsed from greenhouse_board_tokens."""
        return [t.strip() for t in self.greenhouse_board_tokens.split(",") if t.strip()]

    @property
    def lever_slug_list(self) -> list[str]:
        """Returns list of Lever company slugs parsed from lever_company_slugs."""
        return [t.strip() for t in self.lever_company_slugs.split(",") if t.strip()]

    @property
    def ashby_slug_list(self) -> list[str]:
        """Returns list of Ashby company slugs parsed from ashby_company_slugs."""
        return [t.strip() for t in self.ashby_company_slugs.split(",") if t.strip()]

    @property
    def workday_company_list(self) -> list[dict]:
        """Returns list of {tenant, board, wdhost} dicts from workday_companies.

        Format: "tenant:board" or "tenant:board:wdhost" (wdhost defaults to wd1).
        Example: "intel:External,paypal:jobs:wd1"
        """
        results = []
        for entry in self.workday_companies.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":")
            if len(parts) < 2:
                continue
            tenant = parts[0].strip()
            board = parts[1].strip()
            wdhost = parts[2].strip() if len(parts) >= 3 else "wd1"
            results.append({"tenant": tenant, "board": board, "wdhost": wdhost})
        return results

    @property
    def workday_csrf_company_list(self) -> list[dict]:
        """Returns list of {tenant, board, wdhost} dicts for CSRF-protected Workday boards."""
        results = []
        for entry in self.workday_csrf_companies.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":")
            if len(parts) < 2:
                continue
            tenant = parts[0].strip()
            board = parts[1].strip()
            wdhost = parts[2].strip() if len(parts) >= 3 else "wd1"
            results.append({"tenant": tenant, "board": board, "wdhost": wdhost})
        return results

    def _parse_query_list(self, raw: str) -> list[str]:
        return [q.strip() for q in raw.split(",") if q.strip()]

    @property
    def google_query_list(self) -> list[str]:
        return self._parse_query_list(self.google_search_queries)

    @property
    def amazon_query_list(self) -> list[str]:
        return self._parse_query_list(self.amazon_search_queries)

    @property
    def apple_query_list(self) -> list[str]:
        return self._parse_query_list(self.apple_search_queries)

    @property
    def microsoft_query_list(self) -> list[str]:
        return self._parse_query_list(self.microsoft_search_queries)

    @property
    def meta_query_list(self) -> list[str]:
        return self._parse_query_list(self.meta_search_queries)

    @property
    def smartrecruiters_company_list(self) -> list[str]:
        """Returns list of SmartRecruiters company identifiers."""
        return [t.strip() for t in self.smartrecruiters_companies.split(",") if t.strip()]

    @property
    def linkedin_search_list(self) -> list[dict]:
        """Returns list of {keyword, location} dicts parsed from linkedin_searches."""
        results = []
        for entry in self.linkedin_searches.split(","):
            entry = entry.strip()
            if "|" not in entry:
                continue
            keyword, location = entry.split("|", 1)
            results.append({"keyword": keyword.strip(), "location": location.strip()})
        return results


settings = Settings()
