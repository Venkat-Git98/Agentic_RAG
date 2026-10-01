"""
Keeps the Neo4j Aura Free database alive, independently of the backend.

Aura Free pauses a database after 3 days without a write (reads do not count)
and deletes it 30 days after that. The backend already writes a heartbeat every
12 hours, but only while it is running. This script does the same write from
anywhere, so a scheduled job (.github/workflows/neo4j-keepalive.yml runs it
daily) keeps the database alive even when the backend is down.

It also checks that the graph still holds its data and exits with an error if
not, so the scheduled job fails loudly instead of quietly pinging an empty database.

Needs only the `neo4j` package and these environment variables:
    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE (optional)

    python Backend/scripts/neo4j_keepalive.py
"""
import os
import sys

from neo4j import GraphDatabase

EXPECTED_MIN_NODES = 5000   # the loaded graph has about 5,960 nodes


def main() -> int:
    missing = [name for name in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD") if not os.environ.get(name)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        return 2
    database = os.environ.get("NEO4J_DATABASE") or None

    try:
        with GraphDatabase.driver(
            os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
        ) as driver:
            records, _, _ = driver.execute_query("""
                MERGE (k:KeepAlive {id: 'heartbeat'})
                SET k.last_ping = datetime(), k.ping_count = coalesce(k.ping_count, 0) + 1
                RETURN k.ping_count AS pings, toString(k.last_ping) AS at
            """, database_=database)
            pings, at = records[0]["pings"], records[0]["at"]
            records, _, _ = driver.execute_query("MATCH (n) RETURN count(n) AS nodes", database_=database)
            nodes = records[0]["nodes"]
    except Exception as e:
        # A paused database refuses connections: resume it at https://console.neo4j.io
        print(f"Keep-alive FAILED: {type(e).__name__}: {e}")
        return 1

    print(f"Keep-alive write ok: ping #{pings} at {at}; graph has {nodes} nodes.")
    if nodes < EXPECTED_MIN_NODES:
        print(f"Graph looks incomplete: expected at least {EXPECTED_MIN_NODES} nodes. Reload it with "
              "Backend/data_ingestion_pipeline/load_and_embed.py.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
