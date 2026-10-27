#!/usr/bin/env python3
"""
query_aima.py - Fast offline search and excerpt tool for AIMA.pdf (4th Edition).

Designed for COL333 AI assignments:
- Enforces course-taught curriculum boundaries (Chapters 3, 4, 5, 6, 16, 17, 21, 23).
- Returns concise matching snippets with exact page numbers.
- Consumes zero LLM API tokens.

Usage:
    python3 scripts/query_aima.py "quiescence search"
    python3 scripts/query_aima.py "evaluation function" --max-results 5
    python3 scripts/query_aima.py --page 205
    python3 scripts/query_aima.py "alpha beta" --all-pages
"""

import os
import sys
import json
import re
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF_PATH = os.path.join(ROOT, "AIMA.pdf")
CACHE_DIR = os.path.join(ROOT, ".cache")
CACHE_FILE = os.path.join(CACHE_DIR, "aima_index.json")

# Course-approved chapters and page ranges in AIMA 4th Edition
COURSE_RANGES = [
    (81, 127, "Chapter 3: Solving Problems by Searching (Uninformed & Heuristic Search, A*, IDA*)"),
    (128, 163, "Chapter 4: Search in Complex Environments (Local Search, Continuous Spaces, Real-Time Search)"),
    (164, 191, "Chapter 5: Constraint Satisfaction Problems (Backtracking, AC-3, Heuristics)"),
    (192, 225, "Chapter 6: Adversarial Search and Games (Minimax, Alpha-Beta, Cutoffs, Quiescence, MCTS, Expectimax)"),
    (544, 588, "Chapter 16: Making Complex Decisions (MDPs, Value Iteration, Policy Iteration)"),
    (589, 640, "Chapter 17: Multiagent Decision Making (Game Theory, Coordination)"),
    (772, 800, "Chapter 21: Learning Probabilistic Models (Statistical Learning, EM, Naive Bayes)"),
    (840, 873, "Chapter 23: Reinforcement Learning (Passive/Active RL, Q-Learning, TD-Learning)"),
]

def get_chapter_for_page(page_num):
    for start, end, desc in COURSE_RANGES:
        if start <= page_num <= end:
            return desc
    return None

def is_course_page(page_num):
    return get_chapter_for_page(page_num) is not None

def ensure_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    if not os.path.exists(PDF_PATH):
        sys.stderr.write(f"Error: Could not find AIMA.pdf at {PDF_PATH}\n")
        sys.exit(1)

    try:
        import pypdf
    except ImportError:
        sys.stderr.write("Error: pypdf not installed. Please run: pip install pypdf\n")
        sys.exit(1)

    sys.stderr.write("Indexing AIMA.pdf for fast offline search (one-time setup)...\n")
    reader = pypdf.PdfReader(PDF_PATH)
    total_pages = len(reader.pages)

    data = {}
    for i in range(total_pages):
        page_num = i + 1
        text = reader.pages[i].extract_text() or ""
        # Clean text
        text = re.sub(r"\s+", " ", text).strip()
        data[str(page_num)] = text

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    sys.stderr.write(f"Indexed {total_pages} pages into {CACHE_FILE}\n\n")
    return data

def show_page(pages_data, page_num):
    key = str(page_num)
    if key not in pages_data:
        print(f"Page {page_num} is out of bounds (1..{len(pages_data)}).")
        return

    chapter = get_chapter_for_page(page_num)
    scope_tag = f" [COL333 Scope: {chapter}]" if chapter else " [OUTSIDE COL333 SCOPE]"
    print(f"\n{'='*70}\n--- AIMA 4th Ed. Page {page_num}{scope_tag} ---\n{'='*70}\n")
    text = pages_data[key]
    # Format paragraphs
    paragraphs = re.split(r"(?<=\.) +", text)
    formatted = ""
    line = ""
    for p in paragraphs:
        if len(line) + len(p) > 90:
            formatted += line + "\n"
            line = p + " "
        else:
            line += p + " "
    if line:
        formatted += line + "\n"
    print(formatted)

def search_text(pages_data, query, course_only=True, max_results=3, context_chars=250):
    terms = query.strip().lower().split()
    if not terms:
        print("Please provide a query string.")
        return

    # Check for prohibited / out-of-scope triggers to warn the student/agent
    prohibited_patterns = [
        (r"deep\s+q[\s_-]?network|dqn", "Deep Q-Networks / Deep RL are outside course scope (COL333 uses tabular/heuristic search)."),
        (r"pytorch|tensorflow|keras", "Neural network frameworks are strictly disallowed in student code for this assignment."),
        (r"genetic\s+algorithm", "Evolutionary / Genetic Algorithms are outside the scope of COL333 syllabus."),
        (r"scipy\.optimize", "scipy optimization is explicitly disallowed by assignment instructions.")
    ]
    for pattern, warning in prohibited_patterns:
        if re.search(pattern, query.lower()):
            sys.stderr.write(f"\n⚠️  COMPLIANCE WARNING: '{query}' touches techniques outside COL333 course syllabus:\n   -> {warning}\n\n")

    results = []
    phrase_pattern = re.compile(re.escape(query), re.IGNORECASE)

    for page_str, text in pages_data.items():
        page_num = int(page_str)
        chapter = get_chapter_for_page(page_num)
        if course_only and not chapter:
            continue

        lower_text = text.lower()
        # Score matches: phrase match scores highest, all-terms match next
        exact_matches = list(phrase_pattern.finditer(text))
        if exact_matches:
            score = 100 + len(exact_matches) * 10
            match_pos = exact_matches[0].start()
        elif all(term in lower_text for term in terms):
            score = 50 + sum(lower_text.count(t) for t in terms)
            match_pos = lower_text.find(terms[0])
        else:
            continue

        start = max(0, match_pos - context_chars // 2)
        end = min(len(text), match_pos + context_chars // 2)
        snippet = text[start:end].strip()

        results.append({
            "page": page_num,
            "chapter": chapter or "General/Out-of-scope Chapter",
            "score": score,
            "snippet": f"... {snippet} ..."
        })

    results.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n{'='*75}")
    scope_str = "COL333 Whitelisted Chapters" if course_only else "Entire Textbook"
    print(f" Search: '{query}' | Scope: {scope_str} | Matches: {len(results)}")
    print(f"{'='*75}\n")

    if not results:
        print("No matches found within the specified scope.")
        if course_only:
            print("Tip: Use --all-pages to expand search beyond course-taught chapters, or try simpler keywords.")
        return

    for i, r in enumerate(results[:max_results]):
        print(f"[{i+1}] Page {r['page']} | {r['chapter']}")
        print(f"    Excerpt: {r['snippet']}\n")

    print(f"Tip: View full page content with: python3 scripts/query_aima.py --page <page_number>\n")

def main():
    parser = argparse.ArgumentParser(description="Fast, zero-token offline search tool for AIMA.pdf.")
    parser.add_argument("query", nargs="?", default=None, help="Keywords or phrase to search")
    parser.add_argument("--page", type=int, default=None, help="View exact page text")
    parser.add_argument("--max-results", "-n", type=int, default=3, help="Max snippet results (default: 3)")
    parser.add_argument("--all-pages", action="store_true", help="Search entire 1166 pages instead of course-taught chapters")
    args = parser.parse_args()

    pages_data = ensure_cache()

    if args.page is not None:
        show_page(pages_data, args.page)
    elif args.query:
        search_text(pages_data, args.query, course_only=not args.all_pages, max_results=args.max_results)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
