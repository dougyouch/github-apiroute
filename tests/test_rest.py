"""The REST client's typed models against what GitHub actually sends."""

import pytest
from pydantic import ValidationError

from github_apiroute.rest.models.schemas.pull_request_simple_labels_item import (
    PullRequestSimpleLabelsItem,
)

LABEL = {
    "id": 1,
    "node_id": "LA_1",
    "url": "https://api.github.com/repos/o/r/labels/bug",
    "name": "bug",
    "description": None,  # the spec says a string; labels without one come back null
    "color": "d73a4a",
    "default": True,
    "archived_by": None,
}


def test_a_field_the_spec_calls_never_null_accepts_null():
    assert PullRequestSimpleLabelsItem.model_validate(LABEL).description is None


def test_required_fields_must_still_be_present():
    with pytest.raises(ValidationError):
        PullRequestSimpleLabelsItem.model_validate({k: v for k, v in LABEL.items() if k != "name"})
