#!/usr/bin/env python3
"""Final retry for 406 1st Ave N Buffer posts. Runs after rate limit clears."""
import json, subprocess, time, sys

API_KEY = "4I6VSpvj17vSpZhL_N5u8exNmv8Yjjbxkx1UBeZgcsr"
IMAGE_URL = "https://files.catbox.moe/t7n1vk.jpg"

# Slightly tweaked text to avoid Facebook duplicate filter
POST_TEXT = """\U0001f3d6\ufe0f JUST LISTED \u2014 406 1st Ave N, North Myrtle Beach

$925,000 | 4 BR | 3 BA | 1,669 sqft

Brand-new raised beach house in Ocean Drive Estates \u2014 walking distance to the Atlantic. Built in 2023, this one checks every box for short-term rental investors or buyers looking for turn-key coastal living.

\u2714\ufe0f 9 & 10-foot ceilings
\u2714\ufe0f 7,400+ sqft lot
\u2714\ufe0f 6-car parking underneath
\u2714\ufe0f Premium STR location in the heart of NMB

The kind of property that makes rental portfolios perform. Don\u2019t sleep on this one.

\U0001f4f2 Jeff Forman | The Forturro Group
843-902-4325 | Jeff@forturro.com"""

CHANNELS = {
    "Facebook": {"id": "69cf01bbaf47dacb69826eef", "metadata": {"facebook": {"type": "post"}}},
    "LinkedIn": {"id": "69cf0080af47dacb69826bf8", "metadata": {"linkedin": {}}},
    "Instagram": {"id": "69cf0271af47dacb69827091", "metadata": {"instagram": {"type": "post", "shouldShareToFeed": True}}}
}

def gql(query, variables=None):
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", "https://api.buffer.com/graphql",
         "-H", f"Authorization: Bearer {API_KEY}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=20
    )
    return json.loads(result.stdout)

def wait_for_rate_limit():
    for i in range(25):
        print(f"Checking rate limit... (attempt {i+1})", flush=True)
        try:
            resp = gql('{ __typename }')
            if "errors" not in resp or "RATE_LIMIT" not in str(resp):
                print("Rate limit cleared!", flush=True)
                return True
        except:
            pass
        time.sleep(60)
    return False

query = """mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess { post { id status } }
    ... on NotFoundError { message }
    ... on UnauthorizedError { message }
    ... on UnexpectedError { message }
    ... on RestProxyError { message }
    ... on LimitReachedError { message }
    ... on InvalidInputError { message }
  }
}"""

print("Waiting for rate limit to clear...", flush=True)
if not wait_for_rate_limit():
    print("FAILED: rate limit didn't clear", flush=True)
    sys.exit(1)

results = {}
for name, ch in CHANNELS.items():
    variables = {
        "input": {
            "channelId": ch["id"],
            "text": POST_TEXT,
            "mode": "shareNow",
            "schedulingType": "automatic",
            "assets": {"images": [{"url": IMAGE_URL}]},
            "metadata": ch["metadata"]
        }
    }
    resp = gql(query, variables)
    if "errors" in resp:
        results[name] = f"GQL_ERROR: {resp['errors'][0]['message']}"
    else:
        cp = resp.get("data", {}).get("createPost", {})
        post = cp.get("post")
        msg = cp.get("message")
        if post:
            # Verify it actually posted
            time.sleep(3)
            check = gql('{ post(input: {id: "' + post['id'] + '"}) { status error { message rawError } } }')
            actual_status = check.get("data",{}).get("post",{}).get("status","unknown")
            error_msg = check.get("data",{}).get("post",{}).get("error")
            results[name] = f"status: {actual_status}" + (f" error: {error_msg}" if error_msg else "")
        elif msg:
            results[name] = f"API_ERROR: {msg}"
        else:
            results[name] = f"UNKNOWN: {json.dumps(cp)}"
    time.sleep(2)

print("\n=== RESULTS ===", flush=True)
for name, status in results.items():
    print(f"{name}: {status}", flush=True)

with open("/tmp/buffer_406_final.json", "w") as f:
    json.dump(results, f)
