import os

from neo4j import GraphDatabase

from infrastructure.base.result import Result


class CypherDriver:
    driver = None

    @classmethod
    def _get_connect(cls):
        if cls.driver is None:
            cls.driver = GraphDatabase.driver(
                uri=os.getenv("NEO4J_CONNECTOR_URI"),
                auth=(os.getenv("NEO4J_CONNECTOR_AUTH_USER"), os.getenv("NEO4J_CONNECTOR_AUTH_PASSWORD")),
            )
        return cls.driver

    @classmethod
    def _execute_write_cypher(cls, graph, cypher, params=None):
        graph.run(cypher, parameters=params)

    @classmethod
    def _execute_read_cypher(cls, graph, cypher, params=None):
        result = graph.run(cypher, parameters=params)
        return [{k: v for k, v in record.items()} for record in result]

    @classmethod
    def execute_read(cls, cypher: str, params=None):
        session = cls._get_connect().session()
        try:
            results = session.execute_read(cls._execute_read_cypher, cypher, params)
        except Exception:
            session.close()
            return Result.build_error()
        session.close()
        return Result.build_success_with_results(results)

    @classmethod
    def execute_write(cls, cypher: str, params=None):
        session = cls._get_connect().session()
        try:
            session.execute_write(cls._execute_write_cypher, cypher, params)
        except Exception:
            session.close()
            return Result.build_error()
        session.close()
        return Result.build_success()
