from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.models import Organization, Sponsor
from api.seed import seed_founding_data


def test_seed_is_idempotent(db: Session) -> None:
    first = seed_founding_data(db)
    second = seed_founding_data(db)
    assert first == second
    assert db.scalar(select(func.count()).select_from(Organization)) == 2
    sponsors = db.scalars(select(Sponsor)).all()
    assert len(sponsors) == 2
    by_slug = {s.slug: s for s in sponsors}
    assert by_slug["hashtag-india-cary"].status == "draft"
    assert by_slug["cgi"].status == "draft"
    assert by_slug["hashtag-india-cary"].logo_path is None
    assert by_slug["cgi"].logo_path is None


def test_orgs_endpoint_reads_db(client) -> None:
    res = client.get("/v1/orgs")
    assert res.status_code == 200
    body = res.json()
    slugs = {o["slug"] for o in body}
    assert slugs == {"starks", "steelers"}
    starks = next(o for o in body if o["slug"] == "starks")
    assert starks["initial_sponsor"]["name"] == "Hashtag India Cary"
    assert starks["initial_sponsor"]["status"] == "draft"
