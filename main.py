import argparse
import json
from pathlib import Path

from agents import PlannerError, generate_plan
from demo import preview_plan
from models import Settings, WeddingBrief, sample_brief


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a wedding plan from a structured brief.")
    parser.add_argument("--brief", type=Path, help="JSON brief exported from the app")
    parser.add_argument(
        "--preview", action="store_true", help="Use a local template without API calls"
    )
    parser.add_argument("--output", type=Path, help="Save the Markdown plan to this path")
    args = parser.parse_args()
    try:
        brief = (
            WeddingBrief.model_validate_json(args.brief.read_text(encoding="utf-8"))
            if args.brief
            else sample_brief()
        )
        result = preview_plan(brief) if args.preview else generate_plan(brief, Settings.load())
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(result["markdown"], encoding="utf-8")
            print(f"Saved plan: {args.output}")
        else:
            print(result["markdown"])
        return 0
    except (PlannerError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Could not generate the plan: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
