"""The bricks a language model proposed and the rule search kept, stored with where they come from.

    vocabulary/learned.json: [{case, hole, tag, source, extends, model, effect, date}, ...]

A later run of the same case loads them into the dictionary of that hole, so the result does not need the model
again. A stored brick is code from a model: it is compiled each time through the same sandbox as a fresh
proposal (engine.compile_brick: no import, nothing that starts with an underscore, restricted builtins), never
imported as a module. `extends` names the brick its `best(...)` calls (module.function of the conventions).
"""
import importlib
import json
import time
from pathlib import Path
from engine import compile_brick

STORE = Path(__file__).resolve().parent / 'learned.json'


def entries():
    """Every stored brick, oldest first."""
    return json.loads(STORE.read_text(encoding='utf-8')) if STORE.exists() else []


def resolve(name):
    """The function `module.function`, or None."""
    if not name:
        return None
    module, function = name.rsplit('.', 1)
    return getattr(importlib.import_module(module), function)


def bricks(case, hole):
    """{tag: compiled brick} stored for this case and hole."""
    return {e['tag']: compile_brick(e['source'], resolve(e['extends'])) for e in entries()
            if e['case'] == case and e['hole'] == hole}


def save(case, kept, model):
    """Store the bricks a run kept for `case`: kept is {(hole, tag): ((source, extended brick), effect)}."""
    found = [e for e in entries() if e['case'] != case]
    for (hole, tag), ((source, best), effect) in sorted(kept.items()):
        extends = f'{best.__module__}.{best.__name__}' if callable(best) and best.__name__ != '<lambda>' else None
        found.append({'case': case, 'hole': hole, 'tag': tag, 'source': source, 'extends': extends, 'model': model,
                      'effect': f'exact rows (search, held out) {effect}', 'date': time.strftime('%Y-%m-%d')})
    STORE.write_text(json.dumps(found, indent=1) + '\n', encoding='utf-8')
