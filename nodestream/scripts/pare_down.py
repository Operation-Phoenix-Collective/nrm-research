"""Drop loaded patients and centers so the next ingest is the 500-row sample.

Field and Study nodes stay. Deletes run in batches so a full cohort does not
have to fit in one transaction.
"""

import os
import sys

from neo4j import GraphDatabase

BATCH = 1000
LABELS = ("Patient", "Center")


def delete_label(driver, label):
    total = 0
    while True:
        records, _, _ = driver.execute_query(
            f"MATCH (n:{label}) WITH n LIMIT $limit DETACH DELETE n RETURN count(n) AS deleted",
            limit=BATCH,
            database_="neo4j",
        )
        deleted = records[0]["deleted"]
        total += deleted
        if deleted == 0:
            return total


def main():
    missing = [name for name in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD") if not os.environ.get(name)]
    if missing:
        print("Set " + ", ".join(missing) + " in .env")
        return 1
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
        connection_timeout=10,
    )
    try:
        for label in LABELS:
            deleted = delete_label(driver, label)
            print(f"deleted {deleted} {label} nodes")
    finally:
        driver.close()
    print("Field and Study nodes were left in place. Run make ingest for the 500-row sample.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
