from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Mapping, Protocol, TypedDict, TypeVar

from mashumaro.codecs.basic import decode as decode_to_dataclass
from typing_extensions import NotRequired, override

from dbtsl.api.graphql.util import render_query
from dbtsl.api.shared.query_params import (
    AdhocQueryParametersStrict,
    OrderByMetric,
    QueryParameters,
    validate_query_parameters,
)
from dbtsl.models import Dimension, Entity, Measure, Metric
from dbtsl.models.query import QueryId, QueryResult, QueryStatus
from dbtsl.models.saved_query import SavedQuery


class JobStatusVariables(TypedDict):
    """Variables of operations that will get a job's status."""

    query_id: QueryId


class JobStatusResult(Protocol):
    """Result of operations that fetch a job's status."""

    @property
    def status(self) -> QueryStatus:
        """The job status."""
        raise NotImplementedError()


TJobStatusVariables = TypeVar("TJobStatusVariables", bound=JobStatusVariables, covariant=True)

TJobStatusResult = TypeVar("TJobStatusResult", bound=JobStatusResult, covariant=True)


TVariables = TypeVar("TVariables", bound=Mapping[str, Any])
# Need to make TResponse covariant otherwise we can't annotate something like
# def func(a: ProtocolOperation[JobStatusVariables, JobStatusResult]) -> JobStatusResult:
TResponse = TypeVar("TResponse", covariant=True)


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
                ...&fragment
            }
        }
        """
        return render_query(query, Metric.gql_fragments())

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
                ...&fragment
            }
        }
        """
        return render_query(query, Dimension.gql_fragments())

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
                ...&fragment
            }
        }
        """
        return render_query(query, Measure.gql_fragments())

    @override
    def get_request_variables(self, environment_id: int, **kwargs: ListEntitiesOperationVariables) -> Dict[str, Any]:
        return {
            "environmentId": environment_id,
            "metrics": [{"name": m} for m in kwargs["metrics"]],
        }

    @override
    def parse_response(self, data: Dict[str, Any]) -> List[Measure]:
        return decode_to_dataclass(data["measures"], List[Measure])


class ListEntitiesOperation(ProtocolOperation[ListEntitiesOperationVariables, List[Entity]]):
    """List all entities for a given set of metrics."""

    @override
    def get_request_text(self) -> str:
        query = """
        query getEntities($environmentId: BigInt!, $metrics: [MetricInput!]!) {
            entities(environmentId: $environmentId, metrics: $metrics) {
                ...&fragment
            }
        }
        """
        return render_query(query, Entity.gql_fragments())

    @override
    def get_request_variables(self, environment_id: int, **kwargs: ListEntitiesOperationVariables) -> Dict[str, Any]:
        return {
            "environmentId": environment_id,
            "metrics": [{"name": m} for m in kwargs["metrics"]],
        }

    @override
    def parse_response(self, data: Dict[str, Any]) -> List[Entity]:
        return decode_to_dataclass(data["entities"], List[Entity])


class ListSavedQueriesOperation(ProtocolOperation[EmptyVariables, List[SavedQuery]]):
    """List all saved queries."""

    @override
    def get_request_text(self) -> str:
        query = """
        query getSavedQueries($environmentId: BigInt!) {
            savedQueries(environmentId: $environmentId) {
                ...&fragment
            }
        }
        """
        return render_query(query, SavedQuery.gql_fragments())

    @override
    def get_request_variables(self, environment_id: int, **kwargs: ListEntitiesOperationVariables) -> Dict[str, Any]:
        return {"environmentId": environment_id}

    @override
    def parse_response(self, data: Dict[str, Any]) -> List[SavedQuery]:
        return decode_to_dataclass(data["savedQueries"], List[SavedQuery])


def get_query_request_variables(environment_id: int, params: QueryParameters) -> Dict[str, Any]:
    """Get the GraphQL request variables for a given set of query parameters."""
    strict_params = validate_query_parameters(params)  # type: ignore

    shared_vars = {
        "environmentId": environment_id,
        "where": [{"sql": sql} for sql in strict_params.where] if strict_params.where is not None else None,
        "orderBy": [
            {"metric": {"name": clause.name}, "descending": clause.descending}
            if isinstance(clause, OrderByMetric)
            else {"groupBy": {"name": clause.name, "timeGranularity": clause.grain}, "descending": clause.descending}
            for clause in strict_params.order_by
        ]
        if strict_params.order_by is not None
        else None,
        "limit": strict_params.limit,
        "readCache": strict_params.read_cache,
    }

    if isinstance(strict_params, AdhocQueryParametersStrict):
        return {
            "savedQuery": None,
            "metrics": [{"name": m} for m in strict_params.metrics] if strict_params.metrics is not None else None,
            "groupBy": [{"name": g} for g in strict_params.group_by] if strict_params.group_by is not None else None,
            **shared_vars,
        }

    return {
        "environmentId": environment_id,
        "savedQuery": strict_params.saved_query,
        "metrics": None,
        "groupBy": None,
        **shared_vars,
    }


class CreateQueryOperation(ProtocolOperation[QueryParameters, QueryId]):
    """Create a query that will be processed asynchronously."""

    @override
    def get_request_text(self) -> str:
        query = """
        mutation createQuery(
            $environmentId: BigInt!,
            $savedQuery: String,
            $metrics: [MetricInput!],
            $groupBy: [GroupByInput!],
            $where: [WhereInput!],
            $orderBy: [OrderByInput!],
            $limit: Int,
            $readCache: Boolean,
        ) {
            createQuery(
                environmentId: $environmentId,
                savedQuery: $savedQuery,
                metrics: $metrics,
                groupBy: $groupBy,
                where: $where,
                orderBy: $orderBy,
                limit: $limit,
                readCache: $readCache,
            ) {
                queryId
            }
        }
        """
        return query

    @override
    def get_request_variables(self, environment_id: int, **kwargs: QueryParameters) -> Dict[str, Any]:
        # TODO: fix typing
        return get_query_request_variables(environment_id, kwargs)  # type: ignore

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
                ...&fragment
            }
        }
        """
        return render_query(query, QueryResult.gql_fragments())

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


class CompileSqlOperation(ProtocolOperation[QueryParameters, str]):
    """Get the compiled SQL that would be sent to the warehouse by a query."""

    @override
    def get_request_text(self) -> str:
        query = """
        mutation compileSql(
            $environmentId: BigInt!,
            $savedQuery: String,
            $metrics: [MetricInput!],
            $groupBy: [GroupByInput!],
            $where: [WhereInput!],
            $orderBy: [OrderByInput!],
            $limit: Int,
            $readCache: Boolean,
        ) {
            compileSql(
                environmentId: $environmentId,
                savedQuery: $savedQuery,
                metrics: $metrics,
                groupBy: $groupBy,
                where: $where,
                orderBy: $orderBy,
                limit: $limit,
                readCache: $readCache,
            ) {
                sql
            }
        }
        """
        return query

    @override
    def get_request_variables(self, environment_id: int, **kwargs: QueryParameters) -> Dict[str, Any]:
        # TODO: fix typing
        return get_query_request_variables(environment_id, kwargs)  # type: ignore

    @override
    def parse_response(self, data: Dict[str, Any]) -> str:
        return data["compileSql"]["sql"]


class GraphQLProtocol:
    """Holds the GraphQL implementation for each of method in the API.

    This allows us to use sync/async IO transports without rewriting the
    GraphQL logic.
    """

    metrics = ListMetricsOperation()
    dimensions = ListDimensionsOperation()
    measures = ListMeasuresOperation()
    entities = ListEntitiesOperation()
    saved_queries = ListSavedQueriesOperation()
    create_query = CreateQueryOperation()
    get_query_result = GetQueryResultOperation()
    compile_sql = CompileSqlOperation()
