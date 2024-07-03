from __future__ import annotations

import re
from string import Template
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from dbtsl.models.base import GraphQLFragment

query_sub_pat = re.compile(r"[ \t\n]+")


def normalize_query(s: str) -> str:
    """Return a normalized query string.

    This strips newlines, too many whitespaces etc so we can
    make assertions that queries equal each other regarless of indentation.
    """
    return query_sub_pat.subn(" ", s.strip("\n"))[0].strip()


class QueryTemplate(Template):
    """Subclass Template since $ is reserved in GraphQL."""

    delimiter = "&"


def render_query(template_str: str, dependencies: List[GraphQLFragment]) -> str:
    """Return a rendered query from a template and its fragment dependencies.

    The template must have a &fragment which indicates where the main
    fragment should be replaced in the query.

    The main fragment will be dependencies[0].
    """
    template = QueryTemplate(template_str)
    assert len(dependencies) > 0
    template_render = normalize_query(template.substitute(fragment=dependencies[0].name))
    segments = [template_render] + [normalize_query(frag.body) for frag in dependencies]
    return " ".join(segments)
