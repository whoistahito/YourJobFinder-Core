from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, StringConstraints, HttpUrl

from domain.job_posting import JobPostingModel


NonEmptyStr = Annotated[str, StringConstraints(min_length=2, strip_whitespace=True)]


class LinkedInJobPosting(BaseModel):
    # Strict scraper-side model; maps into the unified domain JobPostingModel.
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    title: NonEmptyStr
    company: NonEmptyStr
    location: Optional[str] = None
    link: HttpUrl
    date_posted: Optional[str] = None

    def to_job_posting(self) -> JobPostingModel:
        return JobPostingModel(
            title=self.title,
            company=self.company,
            link=str(self.link),
            location=self.location,
            date_posted=self.date_posted,
        )
