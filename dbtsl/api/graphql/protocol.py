from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Mapping, TypedDict, TypeVar

from mashumaro.codecs.basic import decode as decode_to_dataclass
from typing_extensions import NotRequired, override

from dbtsl.api.shared.query_params import QueryParameters
from dbtsl.models import Dimension, Measure, Metric
from dbtsl.models.query import QueryId, QueryResult

TVariables = TypeVar("TVariables", bound=Mapping[str, Any])
TResponse = TypeVar("TResponse")


class ProtocolOperation(Generic[TVariables, TResponse], ABC):
    """Base class for GraphQL API operations."""

    @abstractmethod
    def get_request_text(self) -> str:
        """Get the GraphQL request text."""
        raise NotImplementedError()

    @abstractmethod
    def get_request_variables(self, environment_id: int, **kwargs: TVariables) -> Dict[str, Any]:
        """Get the GraphQL variables dictionary."""
        raise NotImplementedError()

    @abstractmethod
    def parse_response(self, data: Dict[str, Any]) -> TResponse:
        """Parse the raw response JSON into a pretty Python type."""
        raise NotImplementedError()


class EmptyVariables(TypedDict, total=False):
    """The parameter type for queries that don't need any variables."""

    pass


class ListMetricsOperation(ProtocolOperation[EmptyVariables, List[Metric]]):
    """List all available metrics in available in the Semantic Layer."""

    @override
    def get_request_text(self) -> str:
        query = """
        query getMetrics($environmentId: BigInt!) {
            metrics(environmentId: $environmentId) {
                name
                description
                type
            }
        }
        """
        return query

    @override
    def get_request_variables(self, environment_id: int, **kwargs: EmptyVariables) -> Dict[str, Any]:
        return {"environmentId": environment_id}

    @override
    def parse_response(self, data: Dict[str, Any]) -> List[Metric]:
        return decode_to_dataclass(data["metrics"], List[Metric])


class ListEntitiesOperationVariables(TypedDict):
    """The parameter type for any operation that lists entities."""

    metrics: List[str]


class ListDimensionsOperation(ProtocolOperation[ListEntitiesOperationVariables, List[Dimension]]):
    """List all dimensions for a given set of metrics."""

    @override
    def get_request_text(self) -> str:
        query = """
        query getDimensions($environmentId: BigInt!, $metrics: [MetricInput!]!) {
            dimensions(environmentId: $environmentId, metrics: $metrics) {
                name
                description
                type
            }
        }
        """
        return query

    @override
    def get_request_variables(self, environment_id: int, **kwargs: ListEntitiesOperationVariables) -> Dict[str, Any]:
        return {
            "environmentId": environment_id,
            "metrics": [{"name": m} for m in kwargs["metrics"]],
        }

    @override
    def parse_response(self, data: Dict[str, Any]) -> List[Dimension]:
        return decode_to_dataclass(data["dimensions"], List[Dimension])


class ListMeasuresOperation(ProtocolOperation[ListEntitiesOperationVariables, List[Measure]]):
    """List all measures for a given set of metrics."""

    @override
    def get_request_text(self) -> str:
        query = """
        query getMeasures($environmentId: BigInt!, $metrics: [MetricInput!]!) {
            measures(environmentId: $environmentId, metrics: $metrics) {
                name
                aggTimeDimension
                agg
                expr
            }
        }
        """
        return query

    @override
    def get_request_variables(self, environment_id: int, **kwargs: ListEntitiesOperationVariables) -> Dict[str, Any]:
        return {
            "environmentId": environment_id,
            "metrics": [{"name": m} for m in kwargs["metrics"]],
        }

    @override
    def parse_response(self, data: Dict[str, Any]) -> List[Measure]:
        return decode_to_dataclass(data["measures"], List[Measure])


class CreateQueryOperation(ProtocolOperation[QueryParameters, QueryId]):
    """Create a query that will be processed asynchronously."""

    @override
    def get_request_text(self) -> str:
        query = """
        mutation createQuery(
            $environmentId: BigInt!,
            $metrics: [MetricInput!]!
        ) {
            createQuery(
                environmentId: $environmentId,
                metrics: $metrics
            ) {
                queryId
            }
        }
        """
        return query

    @override
    def get_request_variables(self, environment_id: int, **kwargs: QueryParameters) -> Dict[str, Any]:
        return {
            "environmentId": environment_id,
            "metrics": [{"name": m} for m in kwargs.get("metrics", [])],
            "groupBy": [{"name": g} for g in kwargs.get("group_by", [])],
            "where": [{"sql": sql} for sql in kwargs.get("where", [])],
            "orderBy": [{"name": o} for o in kwargs.get("order_by", [])],
            "limit": kwargs.get("limit", None),
        }

    @override
    def parse_response(self, data: Dict[str, Any]) -> QueryId:
        return QueryId(data["createQuery"]["queryId"])


class GetQueryResultVariables(TypedDict):
    """Variables for `GetQueryResultOperation`."""

    query_id: QueryId
    page_num: NotRequired[int]


class GetQueryResultOperation(ProtocolOperation[GetQueryResultVariables, QueryResult]):
    """Get the results of a query that was already created."""

    @override
    def get_request_text(self) -> str:
        query = """
        query getQueryResults(
            $environmentId: BigInt!,
            $queryId: String!,
            $pageNum: Int!
        ) {
            query(environmentId: $environmentId, queryId: $queryId, pageNum: $pageNum) {
                queryId,
                status,
                sql,
                error,
                totalPages,
                arrowResult
            }
        }
        """
        return query

    @override
    def get_request_variables(self, environment_id: int, **kwargs: GetQueryResultVariables) -> Dict[str, Any]:
        return {
            "environmentId": environment_id,
            "queryId": kwargs["query_id"],
            "pageNum": kwargs.get("page_num", 1),
        }

    @override
    def parse_response(self, data: Dict[str, Any]) -> QueryResult:
        return decode_to_dataclass(data["query"], QueryResult)


class GraphQLProtocol:
    """Holds the GraphQL implementation for each of method in the API.

    This allows us to use sync/async IO transports without rewriting the
    GraphQL logic.
    """

    metrics = ListMetricsOperation()
    measures = ListDimensionsOperation()
    measures = ListMeasuresOperation()
    create_query = CreateQueryOperation()
    get_query_result = GetQueryResultOperation()
