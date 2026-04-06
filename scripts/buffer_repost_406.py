#!/usr/bin/env python3
"""Retry posting 406 1st Ave N listing to Buffer after rate limit clears."""
import json, subprocess, time, sys

API_KEY = "4I6VSpvj17vSpZhL_N5u8exNmv8Yjjbxkx1UBeZgcsr"
IMAGE_URL = "https://files.catbox.moe/t7n1vk.jpg"
FAILED_IDS = ["69d09040bfce933f1f4c7f73", "69d09041bfce933f1f4c7f9b", "69d09043bfce933f1f4c7fce"]

POST_TEXT = """\U0001f3d6\ufe0f NEW LISTING \u2014 406 1st Ave N, North Myrtle Beach

$925,000 | 4 Bed | 3 Bath | 1,669 sqft

Brand-new raised beach house in Ocean Drive Estates \u2014 walking distance to the Atlantic. Built in 2023, this one checks every box for short-term rental investors or buyers who want turn-key coastal living.

\u2714\ufe0f 9 & 10-foot ceilings
\u2714\ufe0f 7,400+ sqft lot
\u2714\ufe0f 6-car parking underneath
\u2714\ufe0f Premium STR location in the heart of NMB

This is the kind of property that makes rental portfolios perform. Don\u2019t sit on this one.

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
    """Poll until rate limit clears, max 20 min."""
    for i in range(20):
        print(f"  Checking rate limit... (attempt {i+1})")
        try:
            resp = gql('{ __typename }')
            if "errors" not in resp or "RATE_LIMIT" not in str(resp):
                print("  Rate limit cleared!")
                return True
        except:
            pass
        time.sleep(60)
    return False

def delete_failed():
    print("Deleting failed posts...")
    for pid in FAILED_IDS:
        try:
            resp = gql(
                'mutation DeletePost($input: DeletePostInput!) { deletePost(input: $input) { ... on PostActionSuccess { post { id } } ... on NotFoundError { message } } }',
                {"input": {"postId": pid}}
            )
            print(f"  {pid}: {resp}")
        except Exception as e:
            print(f"  {pid}: delete error {e}")

def create_posts():
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
    
    results = {}
    for name, ch in CHANNELS.items():
        variables = {
            "input": {
                "channelId": ch["id"],
                "text": POST_TEXT,
                "mode": "shareNow",
                "schedulingType": "notification",
                "assets": {"images": [{"url": IMAGE_URL}]},
                "metadata": ch["metadata"]
            }
        }
        try:
            resp = gql(query, variables)
            if "errors" in resp:
                results[name] = f"GQL_ERROR: {resp['errors'][0]['message']}"
            else:
                cp = resp.get("data", {}).get("createPost", {})
                post = cp.get("post")
                msg = cp.get("message")
                if post:
                    results[name] = f"OK (id: {post['id']}, status: {post['status']})"
                elif msg:
                    results[name] = f"API_ERROR: {msg}"
                else:
                    results[name] = f"UNKNOWN: {json.dumps(cp)}"
        except Exception as e:
            results[name] = f"EXCEPTION: {e}"
        time.sleep(2)  # small delay between posts
    return results

if __name__ == "__main__":
    print("Waiting for Buffer rate limit to clear...")
    if not wait_for_rate_limit():
        print("FAILED: Rate limit didn't clear in 20 min")
        sys.exit(1)
    
    delete_failed()
    time.sleep(3)
    
    print("\nPosting to all channels...")
    results = create_posts()
    for name, status in results.items():
        print(f"  {name}: {status}")
    
    # Write results for pickup
    with open("/tmp/buffer_406_results.json", "w") as f:
        json.dump(results, f)
    print("\nDone!")
