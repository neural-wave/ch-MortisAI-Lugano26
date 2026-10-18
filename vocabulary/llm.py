"""Where a language model plugs in: run.py --llm. Off by default; the final rule never calls a model.

When a part of the data stays unexplained, the engine calls `propose(prompt, hole)` once per hole.
`prompt` is plain text (the same text as results/<case>_prompt.md): the best rule, how often it fails,
the most frequent missed cases, the bricks already tried and real calls of the bricks of each hole.
`propose` returns new bricks as {name: source}; each source defines `def brick(...)`. The engine
compiles them (engine.compile_brick) and keeps one only if it raises the exact matches on the
held-out policies.

This file talks to any OpenAI-compatible server (vLLM, e.g. our Qwen on vast.ai) with the standard
library only. Set the address and the key in the environment, never in a file that is shared:

    export VAST_URL="http://<host>:<port>"     # http, not https
    export VAST_TOKEN="<key>"
    python3 vocabulary/llm.py                   # check the connection
    python3 vocabulary/run.py --llm --spec vocabulary/specs/ablation/t1_no_easter_holidays.json --out vocabulary/results_llm

Optional: LLM_MODEL (default Qwen/Qwen3.8-27B), LLM_N (answers per request, default 2),
LLM_EFFORT (reasoning effort, default medium), LLM_MAX_CALLS (requests per run, default 6),
LLM_TIMEOUT (seconds per request, default 600). Every request and answer is appended to LOG.
"""
import json
import os
import re
import sys
import time
import urllib.request

MODEL = os.environ.get('LLM_MODEL', 'Qwen/Qwen3.8-27B')
N = int(os.environ.get('LLM_N', 2))
EFFORT = os.environ.get('LLM_EFFORT', 'medium')
MAX_CALLS = int(os.environ.get('LLM_MAX_CALLS', 6))  # per run, to keep the rented GPU time bounded
CALLS = 0
TIMEOUT = int(os.environ.get('LLM_TIMEOUT', 600))  # seconds per request; then the search goes on without it
LOG = 'llm_proposals.jsonl'  # run.py puts it next to the report
CODE = re.compile(r'```(?:python|py)?\s*\n(.*?)```', re.S)


def settings():
    """(url, token) from the environment, or None if no model is configured."""
    url, token = os.environ.get('VAST_URL'), os.environ.get('VAST_TOKEN')
    return (url.rstrip('/'), token) if url and token else None


def request(path, body=None, timeout=900):
    """GET (no body) or POST JSON to the server; the parsed answer."""
    url, token = settings()
    data = json.dumps(body).encode() if body is not None else None
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    with urllib.request.urlopen(urllib.request.Request(url + path, data=data, headers=headers), timeout=timeout) as r:
        return json.load(r)


def bricks_in(text):
    """{name: source} for every code block of an answer that defines `brick`."""
    found = {}
    for source in CODE.findall(text or ''):
        if 'def brick' not in source:
            continue
        name = re.search(r'#\s*name:\s*(.+)', source)
        label = name.group(1).strip()[:120] if name else f'brick {len(found) + 1}'
        while label in found:
            label += "'"
        found[label] = source
    return found


def propose(prompt, hole):
    """New bricks for `hole` from the model; {} if no model is configured or the request fails."""
    global CALLS
    if not settings():
        print('  llm: VAST_URL / VAST_TOKEN not set, no proposals', flush=True)
        return {}
    if CALLS >= MAX_CALLS:
        print(f'  llm: {MAX_CALLS} requests made (LLM_MAX_CALLS), no more proposals', flush=True)
        return {}
    CALLS += 1
    body = {'model': MODEL, 'n': N, 'max_tokens': 16000, 'temperature': 1.0, 'top_p': 0.95, 'top_k': 20,
            'reasoning_effort': EFFORT,
            'messages': [{'role': 'user', 'content': f'{prompt}\n\nThe hole to extend: `{hole}`.'}]}
    started = time.time()
    print(f'  llm: asking the model for new bricks for {hole} ({N} answers, usually 1-5 minutes) ...', flush=True)
    try:
        answer = request('/v1/chat/completions', body, timeout=TIMEOUT)
    except Exception as error:  # the search goes on without proposals
        print(f'  llm: request failed: {error}', flush=True)
        return {}
    if not any(c['message'].get('content') for c in answer.get('choices', [])) and EFFORT != 'low':
        print('  llm: every answer is empty (the reasoning used all tokens); asking once more with effort low', flush=True)
        try:
            answer = request('/v1/chat/completions', {**body, 'reasoning_effort': 'low'}, timeout=TIMEOUT)
        except Exception as error:  # the search goes on without proposals
            print(f'  llm: request failed: {error}', flush=True)
            return {}
    found = {}
    for i, choice in enumerate(answer.get('choices', []), 1):
        for name, source in bricks_in(choice['message'].get('content')).items():
            found[f'{name} (answer {i})'] = source
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'hole': hole, 'seconds': round(time.time() - started, 1), 'prompt': body['messages'][0]['content'],
                            'answers': [c['message'].get('content') for c in answer.get('choices', [])],
                            'bricks': found}) + '\n')
    print(f'  llm: {len(found)} bricks proposed for {hole} in {time.time() - started:.0f} s', flush=True)
    return found


if __name__ == '__main__':  # connection check
    if not settings():
        sys.exit('set VAST_URL and VAST_TOKEN first (see the docstring)')
    print('models:', [m['id'] for m in request('/v1/models', timeout=30)['data']])
    reply = request('/v1/chat/completions', {'model': MODEL, 'max_tokens': 2000, 'reasoning_effort': EFFORT,
                                             'messages': [{'role': 'user', 'content': 'Reply with the word: ready'}]})
    print('answer:', reply['choices'][0]['message'].get('content'))
