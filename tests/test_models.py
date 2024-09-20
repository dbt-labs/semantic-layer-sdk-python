from dataclasses import dataclass
from typing import List

import pytest
from mashumaro.codecs.basic import decode

from dbtsl.api.graphql.util import normalize_query
from dbtsl.api.shared.query_params import QueryParameters, validate_query_parameters
from dbtsl.models.base import BaseModel, GraphQLFragmentMixin
from dbtsl.models.base import snake_case_to_camel_case as stc


def test_snake_case_to_camel_case() -> None:
    assert stc("hello") == "hello"
    assert stc("hello_world") == "helloWorld"
    assert stc("Hello_world") == "HelloWorld"
    assert stc("hello world") == "hello world"
    assert stc("helloWorld") == "helloWorld"


def test_base_model_auto_alias() -> None:
    @dataclass
    class SubModel(BaseModel):
        hello_world: str

    BaseModel._apply_aliases()

    data = {
        "helloWorld": "asdf",
    }

    model = SubModel.from_dict(data)
    assert model.hello_world == "asdf"

    codec_model = decode(data, SubModel)
    assert codec_model.hello_world == "asdf"


def test_graphql_fragment_mixin() -> None:
    @dataclass
    class A(BaseModel, GraphQLFragmentMixin):
        foo_bar: str

    @dataclass
    class B(BaseModel, GraphQLFragmentMixin):
        hello_world: str
        baz: str
        a: A
        many_a: List[A]

    a_fragments = A.gql_fragments()
    assert len(a_fragments) == 1
    a_fragment = a_fragments[0]

    a_expect = normalize_query("""
    fragment fragmentA on A {
        fooBar
    }
    """)
    assert a_fragment.name == "fragmentA"
    assert a_fragment.body == a_expect

    b_fragments = B.gql_fragments()
    assert len(b_fragments) == 2
    b_fragment = b_fragments[0]

    b_expect = normalize_query("""
    fragment fragmentB on B {
        helloWorld
        baz
        a {
            ...fragmentA
        }
        manyA {
            ...fragmentA
        }
    }
    """)
    assert b_fragment.name == "fragmentB"
    assert b_fragment.body == b_expect
    assert b_fragments[1] == a_fragment


def test_validate_query_params_adhoc_query_valid() -> None:
    p: QueryParameters = {
        "metrics": ["a", "b"],
        "group_by": ["a", "b"],
    }
    validate_query_parameters(p)


def test_validate_query_params_saved_query_valid() -> None:
    p: QueryParameters = {"saved_query": "a"}
    validate_query_parameters(p)


def test_validate_query_params_adhoc_query_no_metrics() -> None:
    p: QueryParameters = {
        "metrics": [],
        "group_by": ["a", "b"],
    }
    with pytest.raises(ValueError):
        validate_query_parameters(p)


def test_validate_query_params_adhoc_query_no_group_by() -> None:
    p: QueryParameters = {
        "metrics": ["a", "b"],
        "group_by": [],
    }
    with pytest.raises(ValueError):
        validate_query_parameters(p)


def test_validate_query_params_adhoc_and_saved_query() -> None:
    p: QueryParameters = {"metrics": ["a", "b"], "group_by": ["a", "b"], "saved_query": "a"}
    with pytest.raises(ValueError):
        validate_query_parameters(p)
