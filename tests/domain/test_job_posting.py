import dataclasses

import pytest

from domain.job_posting import JobPostingModel


def test_optional_fields_default_to_none():
    posting = JobPostingModel(title="Python Dev", company="Acme", link="https://x/1")

    assert posting.location is None
    assert posting.date_posted is None
    assert posting.employment_type is None
    assert posting.description is None


def test_frozen_value_object_cannot_be_mutated():
    posting = JobPostingModel(title="Py", company="A", link="https://x/1", description="d")

    with pytest.raises(dataclasses.FrozenInstanceError):
        posting.description = None
