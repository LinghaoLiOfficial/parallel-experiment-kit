from infrastructure.graph.cypher_driver import CypherDriver


cypher_driver = CypherDriver()


class AIExposureMapper:
    @classmethod
    def match_all_tech_en_name_and_keyword_list_mappings(cls, params):
        cypher = """
            MATCH (n:task {task_id: $task_id})-[*1]-(e:tech)
            RETURN e
        """
        return cypher_driver.execute_read(cypher, params)

    @classmethod
    def merge_ai_tech_node(cls, params):
        cypher = """
            MATCH (n:task {task_id: $task_id})
            MERGE (e:tech {tech_en_name: $en_name})
            ON CREATE SET e.tech_zh_name = $zh_name,
                          e.tech_id = $tech_id,
                          e.core_function = $core_function,
                          e.research_application = $research_application,
                          e.tech_maturity_mapping = $tech_maturity_mapping,
                          e.keyword_list = $keyword_list,
                          e.keyword_id_list = $keyword_id_list
            MERGE (n)-[:r]-(e)
        """
        return cypher_driver.execute_write(cypher, params)

    @classmethod
    def match_next_nodes(cls, node_type, node_property, next_node_type, params):
        cypher = f"""
            MATCH (n:{node_type} {{{node_property}: ${node_property}}})-[]->(m:{next_node_type} {{belong: $belong}})
            RETURN m
        """
        return cypher_driver.execute_read(cypher, params)

    @classmethod
    def merge_committee_theme_chain(cls, params):
        cypher = """
            MATCH (n:task {task_id: $task_id})
            MERGE (a:domain {name: $domain_name})
            ON CREATE SET a.gid = $domain_id, a.belong = 'committee'
            MERGE (n)-[:r]-(a)
            MERGE (b:field {name: $field_name})
            ON CREATE SET b.gid = $field_id, b.belong = 'committee'
            MERGE (a)-[:r]-(b)
            MERGE (c:subfield {name: $subfield_name})
            ON CREATE SET c.gid = $subfield_id, c.belong = 'committee'
            MERGE (b)-[:r]-(c)
        """
        return cypher_driver.execute_write(cypher, params)

    @classmethod
    def merge_openalex_theme_chain(cls, params):
        cypher = """
            MATCH (n:task {task_id: $task_id})
            MERGE (a:domain {name: $domain_name})
            ON CREATE SET a.gid = $domain_id, a.belong = 'openalex'
            MERGE (n)-[:r]-(a)
            MERGE (b:field {name: $field_name})
            ON CREATE SET b.gid = $field_id, b.belong = 'openalex'
            MERGE (a)-[:r]-(b)
            MERGE (c:subfield {name: $subfield_name})
            ON CREATE SET c.gid = $subfield_id, c.belong = 'openalex'
            MERGE (b)-[:r]-(c)
            MERGE (d:topic {name: $topic_name})
            ON CREATE SET d.gid = $topic_id, d.summary = $topic_summary, d.belong = 'openalex'
            MERGE (c)-[:r]-(d)
        """
        return cypher_driver.execute_write(cypher, params)

    @classmethod
    def merge_theme_node(cls, params):
        cypher = """
            MATCH (d:topic {name: $topic_name})
            MERGE (e:theme {name: $theme_name})
            ON CREATE SET e.belong = 'openalex'
            MERGE (d)-[:r]-(e)
        """
        return cypher_driver.execute_write(cypher, params)

    @classmethod
    def merge_root_node(cls, params):
        cypher = "MERGE (n:task {task_id: $task_id})"
        return cypher_driver.execute_write(cypher, params)
