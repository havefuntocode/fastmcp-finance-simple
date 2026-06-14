"""
umsatz_server_pg.py
FastMCP Server für Quartalsumsätze – stdio Transport
Datenbank: finance_db (PostgreSQL)
Start: wird automatisch von Claude Desktop gestartet
Zugangsdaten: werden von Claude Desktop via claude_desktop_config.json übergeben
"""

from mcp.server.fastmcp import FastMCP
import psycopg2
import psycopg2.extras  # RealDictCursor
import os

# ── Instanz ────────────────────────────────────────────────────
mcp = FastMCP(
    "Umsatz-Server-PG",
    instructions="""
        Dieser Server stellt Quartalsumsätze aus der PostgreSQL-Datenbank 
        finance_db bereit. Verwende get_chart_data um Umsätze abzufragen 
        und als Balkendiagramm darzustellen.
    """
)


# ── DB-Verbindung ──────────────────────────────────────────────
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "finance_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )

# ── Hilfsfunktion: SQL-Abfrage ─────────────────────────────────
def _query_quartalsumsatz(jahr: int) -> list[dict]:
    conn   = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        SELECT
            jahr,
            CEIL(monat / 3.0)::INT  AS quartal,
            SUM(umsatz)             AS umsatz
        FROM monatsumsatz
        WHERE jahr = %s
        GROUP BY jahr, quartal
        ORDER BY quartal
    """, (jahr,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "jahr":    row["jahr"],
            "quartal": row["quartal"],
            "umsatz":  float(row["umsatz"]),
        }
        for row in rows
    ]

# ── Mapping: DB-Rows → Chart.js dataset ───────────────────────
def _build_chart_data(rows: list[dict], jahr: int) -> dict:
    
    return {
    "type": "bar",
    "data": {
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "datasets": [
            {
                "label": f"Quartalsumsatz {jahr}",
                "data": [row["umsatz"] for row in rows],
                "backgroundColor": "rgba(59,139,212,0.75)",
                "borderColor": "#3B8BD4",
                "borderWidth": 1,
                "borderRadius": 4
            }
        ]
    },
    "options": {
        "scales": {
            "y": {
                "title": {
                    "display": True,
                    "text": "Umsatz in €"
                },
                "beginAtZero": True
            }
        }
    }
}

# ── MCP Tool ───────────────────────────────────────────────────
@mcp.tool()
def get_chart_data(jahr: int) -> dict:
    """
    Liefert ein fertiges Chart.js-Datenobjekt mit Quartalsumsätzen für ein Jahr.
    Parameter:
        jahr: Das gewünschte Jahr (z.B. 2024 oder 2025). Pflichtangabe.
    """
    rows = _query_quartalsumsatz(jahr)
    return _build_chart_data(rows, jahr)

# ── Start ──────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
