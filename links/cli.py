
import typer

app = typer.Typer()

@app.command()
def wikipedia_admins(limit: int = 200, active_days: int = 30):
    print(f"Fetching {limit} Wikipedia admins active in last {active_days} days...")

@app.command()
def build_links(window: int = 30):
    print(f"Building links with window={window} days...")

@app.command()
def export_graph(format: str = "json"):
    print(f"Exporting graph in {format} format...")

if __name__ == "__main__":
    app()
