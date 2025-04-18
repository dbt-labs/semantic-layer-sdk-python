import dataclasses as dc
import inspect
import warnings
from enum import Enum
from typing import List, Optional, Union

import pytest
from mashumaro.codecs.basic import decode
from typing_extensions import override

import dbtsl.models as ALL_EXPORTED_MODELS
from dbtsl.api.graphql.util import normalize_query
from dbtsl.api.shared.query_params import (
    AdhocQueryParametersStrict,
    GroupByParam,
    GroupByType,
    OrderByGroupBy,
    OrderByMetric,
    QueryParameters,
    SavedQueryQueryParametersStrict,
    validate_order_by,
    validate_query_parameters,
)
from dbtsl.models.base import BaseModel, DeprecatedMixin, FlexibleEnumMeta, GraphQLFragmentMixin
from dbtsl.models.base import snake_case_to_camel_case as stc


def test_snake_case_to_camel_case() -> None:
    assert stc("hello") == "hello"
    assert stc("hello_world") == "helloWorld"
    assert stc("Hello_world") == "HelloWorld"
    assert stc("hello world") == "hello world"
    assert stc("helloWorld") == "helloWorld"


def test_FlexibleEnumMeta_parse_unknown_value() -> None:
    """Make sure FlexibleEnumMeta classes parse unknown values without error."""

    class EnumTest(Enum, metaclass=FlexibleEnumMeta):
        A = "A"
        B = "B"
        UNKNOWN = "UNKNOWN"

    assert EnumTest("A") == EnumTest.A
    assert EnumTest("B") == EnumTest.B
    assert EnumTest("test") == EnumTest.UNKNOWN


def test_FlexibleEnumMeta_subclass_with_invalid_unknown_attribute() -> None:
    """Make sure we'll raise an error whenever a flexible enum isn't declared properly."""
    with pytest.raises(AssertionError):

        class EnumTestNoUnknown(Enum, metaclass=FlexibleEnumMeta):
            A = "A"

        _ = EnumTestNoUnknown

    with pytest.raises(AssertionError):

        class EnumTestInvalidUnknown(Enum, metaclass=FlexibleEnumMeta):
            A = "A"
            UNKNOWN = "invalid_value"

        _ = EnumTestInvalidUnknown


def test_all_enum_models_are_flexible() -> None:
    """Make sure we didn't forget to make any enum type flexible."""
    exported_enum_classes = inspect.getmembers(
        ALL_EXPORTED_MODELS, lambda member: (inspect.isclass(member) and issubclass(member, Enum))
    )
    for enum_class_name, _ in exported_enum_classes:
        msg = f"Enum {enum_class_name} needs to have FlexibleEnumMeta metaclass."
        assert enum_class_name in FlexibleEnumMeta._subclass_registry, msg


def test_base_model_auto_alias() -> None:
    @dc.dataclass
    class SubModel(BaseModel):
        hello_world: str

    BaseModel._register_subclasses()

    data = {
        "helloWorld": "asdf",
    }

    model = SubModel.from_dict(data)
    assert model.hello_world == "asdf"

    codec_model = decode(data, SubModel)
    assert codec_model.hello_world == "asdf"


@dc.dataclass
class A(BaseModel, GraphQLFragmentMixin):
    foo_bar: str


@dc.dataclass
class B(BaseModel, GraphQLFragmentMixin):
    hello_world: str
    baz: str
    optional_str: Optional[str]
    str_or_int: Union[str, int]
    eager_a: A
    not_lazy_optional_a: Optional[A] = dc.field(metadata={GraphQLFragmentMixin.NOT_LAZY: True})
    lazy_a: Optional[A] = None
    many_a: List[A] = dc.field(default_factory=list)

    def _load_lazy_a(self) -> A:
        return A(foo_bar="a")

    def _load_many_a(self) -> List[A]:
        return [A(foo_bar="a1"), A(foo_bar="a2")]


GraphQLFragmentMixin._register_subclasses()


def test_graphql_fragment_mixin_register_subclasses() -> None:
    GraphQLFragmentMixin._register_subclasses()
    assert A._lazy_loadable_fields == set()
    assert B._lazy_loadable_fields == {"lazy_a", "many_a"}


def test_graphql_fragment_mixin_lazy_loadable_fields_properties() -> None:
    errors: List[str] = []
    for model in GraphQLFragmentMixin.__subclasses__():
        for field in dc.fields(model):
            if field.name not in model._lazy_loadable_fields:
                continue

            field_name = f"{model.__name__}.{field.name}"

            if field.default == dc.MISSING and field.default_factory == dc.MISSING:
                errors.append(f"{field_name} is lazy-loadable but has no default")

            if not hasattr(model, f"_load_{field.name}"):
                errors.append(f"{field_name} is lazy-loadable but has no loader method")

    error_msg = "\n".join(errors)
    assert len(errors) == 0, error_msg


def test_graphql_fragment_mixin_eager() -> None:
    a_fragments = A.gql_fragments(lazy=False)
    assert len(a_fragments) == 1
    a_fragment = a_fragments[0]

    a_expect = normalize_query("""
    fragment fragmentA on A {
        fooBar
    }
    """)
    assert a_fragment.name == "fragmentA"
    assert a_fragment.body == a_expect
    assert not a_fragment.lazy

    b_fragments = B.gql_fragments(lazy=False)
    assert len(b_fragments) == 2
    b_fragment = b_fragments[0]

    b_expect = normalize_query("""
    fragment fragmentB on B {
        helloWorld
        baz
        optionalStr
        strOrInt
        eagerA {
            ...fragmentA
        }
        notLazyOptionalA {
            ...fragmentA
        }
        lazyA {
            ...fragmentA
        }
        manyA {
            ...fragmentA
        }
    }
    """)
    assert b_fragment.name == "fragmentB"
    assert b_fragment.body == b_expect
    assert not b_fragment.lazy
    assert b_fragments[1] == a_fragment


def test_graphql_fragment_mixin_lazy() -> None:
    a_fragments = A.gql_fragments(lazy=True)
    assert len(a_fragments) == 1
    a_fragment = a_fragments[0]

    a_expect = normalize_query("""
    fragment fragmentA on A {
        fooBar
    }
    """)
    assert a_fragment.name == "fragmentA"
    assert a_fragment.body == a_expect
    assert a_fragment.lazy

    b_fragments = B.gql_fragments(lazy=True)
    assert len(b_fragments) == 2
    b_fragment = b_fragments[0]

    b_expect = normalize_query("""
    fragment fragmentB on B {
        helloWorld
        baz
        optionalStr
        strOrInt
        eagerA {
            ...fragmentA
        }
        notLazyOptionalA {
            ...fragmentA
        }
    }
    """)
    assert b_fragment.name == "fragmentB"
    assert b_fragment.body == b_expect
    assert b_fragment.lazy
    assert b_fragments[1] == a_fragment


def test_DeprecatedMixin() -> None:
    msg = "i am deprecated :("

    class MyDeprecatedClass(DeprecatedMixin):
        @override
        @classmethod
        def _deprecation_message(cls) -> str:
            return msg

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        _ = MyDeprecatedClass()
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert msg == str(w[0].message)


def test_attr_deprecation_warning() -> None:
    msg = "i am deprecated :("

    @dc.dataclass(frozen=True)
    class MyClassWithDeprecatedField(BaseModel):
        its_fine: bool = True
        oh_no: bool = dc.field(default=False, metadata={BaseModel.DEPRECATED: msg})

    BaseModel._register_subclasses()

    m = MyClassWithDeprecatedField()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        _ = m.its_fine
        assert len(w) == 0

        _ = m.oh_no
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert msg == str(w[0].message)


def test_validate_order_by_params_passthrough_OrderByMetric() -> None:
    i = OrderByMetric(name="asdf", descending=True)
    r = validate_order_by([], [], i)
    assert r == i


def test_validate_order_by_params_passthrough_OrderByGroupBy() -> None:
    i = OrderByGroupBy(name="asdf", grain=None, descending=True)
    r = validate_order_by([], [], i)
    assert r == i


def test_validate_order_by_params_ascending() -> None:
    r = validate_order_by(["metric"], [], "+metric")
    assert r == OrderByMetric(name="metric", descending=False)


def test_validate_order_by_params_descending() -> None:
    r = validate_order_by(["metric"], [], "-metric")
    assert r == OrderByMetric(name="metric", descending=True)


def test_validate_order_by_params_metric() -> None:
    r = validate_order_by(["a"], ["b"], "a")
    assert r == OrderByMetric(
        name="a",
        descending=False,
    )


def test_validate_order_by_params_group_by() -> None:
    r = validate_order_by(["a"], ["b"], "b")
    assert r == OrderByGroupBy(
        name="b",
        grain=None,
        descending=False,
    )


def test_validate_order_by_not_found() -> None:
    with pytest.raises(ValueError):
        validate_order_by(["a"], ["b"], "c")


def test_validate_query_params_adhoc_query_valid_metrics_and_groupby() -> None:
    p: QueryParameters = {
        "metrics": ["a", "b"],
        "group_by": ["c", "d"],
        "order_by": ["a"],
        "where": ["1=1"],
        "limit": 1,
        "read_cache": False,
    }
    r = validate_query_parameters(p)
    assert isinstance(r, AdhocQueryParametersStrict)
    assert r.metrics == ["a", "b"]
    assert r.group_by == ["c", "d"]
    assert r.order_by == [OrderByMetric(name="a")]
    assert r.where == ["1=1"]
    assert r.limit == 1
    assert not r.read_cache


def test_validate_query_params_adhoc_query_valid_only_groupby() -> None:
    p: QueryParameters = {"group_by": ["gb"], "limit": 1, "where": ["1=1"], "order_by": ["gb"], "read_cache": False}
    r = validate_query_parameters(p)
    assert isinstance(r, AdhocQueryParametersStrict)
    assert r.metrics is None
    assert r.group_by == ["gb"]
    assert r.order_by == [OrderByGroupBy(name="gb", grain=None)]
    assert r.where == ["1=1"]
    assert r.limit == 1
    assert not r.read_cache


def test_validate_query_params_saved_query_valid() -> None:
    p: QueryParameters = {
        "saved_query": "a",
        "order_by": [OrderByMetric(name="b")],
        "where": ["1=1"],
        "limit": 1,
        "read_cache": False,
    }
    r = validate_query_parameters(p)
    assert isinstance(r, SavedQueryQueryParametersStrict)
    assert r.saved_query == "a"
    assert r.order_by == [OrderByMetric(name="b")]
    assert r.where == ["1=1"]
    assert r.limit == 1
    assert not r.read_cache


def test_validate_query_params_saved_query_group_by() -> None:
    p: QueryParameters = {
        "saved_query": "sq",
        "group_by": ["a", "b"],
    }
    with pytest.raises(ValueError):
        validate_query_parameters(p)


def test_validate_query_params_adhoc_and_saved_query() -> None:
    p: QueryParameters = {"metrics": ["a", "b"], "group_by": ["a", "b"], "saved_query": "a"}
    with pytest.raises(ValueError):
        validate_query_parameters(p)


def test_validate_query_params_no_query() -> None:
    p: QueryParameters = {"limit": 1, "where": ["1=1"], "order_by": ["a"], "read_cache": False}
    with pytest.raises(ValueError):
        validate_query_parameters(p)


def test_validate_query_params_group_by_param_dimension() -> None:
    p: QueryParameters = {
        "group_by": [GroupByParam(name="a", grain="day", type=GroupByType.DIMENSION)],
        "order_by": ["a"],
    }
    r = validate_query_parameters(p)
    assert isinstance(r, AdhocQueryParametersStrict)
    assert r.group_by == [GroupByParam(name="a", grain="day", type=GroupByType.DIMENSION)]


def test_validate_query_params_group_by_param_entity() -> None:
    p: QueryParameters = {"group_by": [GroupByParam(name="a", grain="day", type=GroupByType.ENTITY)], "order_by": ["a"]}
    r = validate_query_parameters(p)
    assert isinstance(r, AdhocQueryParametersStrict)
    assert r.group_by == [GroupByParam(name="a", grain="day", type=GroupByType.ENTITY)]


def test_validate_missing_query_params_group_by_param() -> None:
    p: QueryParameters = {
        "group_by": [GroupByParam(name="b", grain="day", type=GroupByType.DIMENSION)],
        "order_by": ["a"],
    }
    with pytest.raises(ValueError):
        validate_query_parameters(p)
