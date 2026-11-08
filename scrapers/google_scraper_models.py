from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, HttpUrl

from domain.job_posting import JobPostingModel


NonEmptyStr = Annotated[str, StringConstraints(min_length=2, strip_whitespace=True)]

class GoogleJobPosting(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    title: NonEmptyStr
    company: NonEmptyStr
    location: Optional[str] = None
    link: HttpUrl
    date_posted: Optional[str] = Field(default=None, alias="datePosted")
    employment_type: Optional[str] = Field(default=None, alias="employmentType")
    description: Optional[str] = None

    def to_job_posting(self) -> JobPostingModel:
        # Scraper-owned map: GoogleJobPosting → unified domain JobPostingModel.
        return JobPostingModel(
            title=self.title,
            company=self.company,
            link=str(self.link),
            location=self.location,
            date_posted=self.date_posted,
            employment_type=self.employment_type,
            description=self.description,
        )


class GoogleScrapeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    query: str = ""
    jobs: List[GoogleJobPosting] = Field(default_factory=list)
    url: Optional[str] = None
    original_html_length: Optional[int] = Field(default=None, alias="originalHtmlLength")

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "GoogleScrapeResponse":
        from logger_utils import create_logger
        logger = create_logger("Google Scraper")
        valid_jobs = []
        for raw_job in data.get("jobs", []):
            try:
                valid_jobs.append(GoogleJobPosting.model_validate(raw_job))
            except Exception as e:
                logger.warning(f"Skipping job due to validation error: {e}")
        data = {**data, "jobs": valid_jobs}
        return cls.model_validate(data)

    def to_job_postings(self) -> List[JobPostingModel]:
        return [job.to_job_posting() for job in self.jobs]
