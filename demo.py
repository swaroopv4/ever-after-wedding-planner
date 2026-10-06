from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from models import WeddingBrief

BUDGET_CATEGORIES = [
    ("Venue + catering", 45),
    ("Photography + video", 10),
    ("Flowers + design", 8),
    ("Music + entertainment", 7),
    ("Attire + beauty", 6),
    ("Planning + coordination", 5),
    ("Guest transport + stationery", 4),
    ("Ceremony + other essentials", 5),
    ("Contingency (including unquoted fees)", 10),
]


def budget_rows(brief: WeddingBrief) -> list[dict]:
    rows = []
    remaining = brief.budget
    for category, pct in BUDGET_CATEGORIES[:-1]:
        amount = (brief.budget * Decimal(pct) / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        remaining -= amount
        rows.append({"category": category, "percent": pct, "amount": amount})
    rows.append({"category": BUDGET_CATEGORIES[-1][0], "percent": 10, "amount": remaining})
    return rows


def preview_plan(brief: WeddingBrief) -> dict:
    rows = budget_rows(brief)
    table = "\n".join(
        f"| {r['category']} | {r['percent']}% | {brief.currency} {r['amount']:,.2f} |" for r in rows
    )
    today = date.today()
    days = (brief.wedding_date - today).days
    milestones = []
    for fraction, task in [
        (0, "Agree on priorities and request itemized venue proposals"),
        (0.2, "Confirm the venue, catering and essential vendors after quote review"),
        (0.45, "Set the design direction and send guest information"),
        (0.7, "Finalize the menu, accessibility and transport plan"),
        (0.9, "Confirm guest count, seating, vendor schedule and weather backup"),
        (1, "Wedding day: coordinator handles arrivals, ceremony and reception"),
    ]:
        when = today + timedelta(days=round(days * fraction))
        milestones.append(f"- **{when:%b %d, %Y}** — {task}.")
    timeline = "\n".join(milestones)
    text = f"""# Wedding plan for {brief.couple}

> **Preview mode — illustrative planning template.** No AI models or web search were used.
> All allocations are starting assumptions, not local quotes. Venue availability is unverified.

## Executive summary
Plan a {brief.event_scope.lower()} in **{brief.location}** on **{brief.wedding_date:%B %d, %Y}**
for **{brief.guests} guests**, within **{brief.currency} {brief.budget:,.2f}**.
Prioritize {", ".join(brief.priorities) or "a balanced guest experience"}.

## Planning concept
Use a {", ".join(brief.styles).lower() or "personal"} direction, consistent across the ceremony,
table settings and reception. Spend first on guest comfort, food and the setting.
Must-haves to accommodate: {brief.must_haves or "Discuss with the couple."}
Cultural and family considerations: {brief.cultural_details or "Confirm meaningful traditions."}

## Venue and vendor shortlist
Live research will replace these venue concepts with sourced options.

| Venue concept | Why consider it | What to verify |
| --- | --- | --- |
| Garden or estate | One setting for the day | Step-free access, capacity and rain plan |
| Hotel or resort | Accommodation and catering | Room blocks, inclusions and minimums |
| Restaurant or event space | Focus on food | Exclusive use, noise limits and ceremony space |

Request comparable, itemized proposals from venues, caterers, photographers, florists and musicians.
Avoid paying deposits until the full cost, cancellation terms and date are confirmed.

## Budget allocation
These are **illustrative allocations**, not price predictions. Check taxes, service charges,
rentals and vendor travel inside each category before committing.

| Category | Share | Allocation |
| --- | ---: | ---: |
{table}
| **Total** | **100%** | **{brief.currency} {brief.budget:,.2f}** |

## Planning timeline
{timeline}

{"With a short lead time, combine these steps and verify availability first." if days < 90 else ""}

## Guest experience and wedding-day outline
- Share arrival instructions, dietary options and accessible routes in advance.
- Suggested sequence: arrivals → ceremony → refreshments and photos → dinner → speeches → dancing.
- Allow transition time and appoint one coordinator as the vendor contact.
- Constraints to resolve: {brief.constraints or "Confirm mobility, dietary and transport needs."}

## Risks and tradeoffs
- Outdoor events need an indoor or covered backup with its own cost allowance.
- Keep contingency available until final invoices; reduce design complexity before guest comfort.
- Confirm vendor availability, deposits, overtime, travel and cancellation terms in writing.

## Next steps and open questions
1. Is the date fixed, and which nearby alternatives are acceptable?
2. Does the budget include rings, honeymoon, accommodation or only the listed event scope?
3. Which three details matter most if quotes exceed the allocation?
4. How many guests need accommodation, transport or accessibility support?
5. Add Groq and Tavily keys, select Live research and generate a sourced plan.
"""
    return {
        "markdown": text.strip(),
        "sources": [],
        "events": ["Built an illustrative template locally; no external requests"],
        "searches": 0,
        "mode": "Preview",
        "model": "Local template",
    }
