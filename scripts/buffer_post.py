#!/usr/bin/env python3
"""
Buffer social media posting script.
Usage: python3 buffer_post.py --text "Post text" --image /path/to/image.jpg [--channels fb,li,ig]

Handles: image upload to public host, posting to all channels, status verification.
"""
import json, subprocess, sys, time, argparse, os

# Load API key
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env.buffer")
API_KEY = None
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            if line.startswith("BUFFER_API_KEY="):
                API_KEY = line.strip().split("=", 1)[1]
                break

if not API_KEY:
    print("ERROR: Could not load BUFFER_API_KEY from .env.buffer")
    sys.exit(1)

CHANNELS = {
    "fb": {
        "name": "Facebook",
        "id": "69cf01bbaf47dacb69826eef",
        "metadata": {"facebook": {"type": "post"}}
    },
    "li": {
        "name": "LinkedIn",
        "id": "69cf0080af47dacb69826bf8",
        "metadata": {"linkedin": {}}
    },
    "ig": {
        "name": "Instagram",
        "id": "69cf0271af47dacb69827091",
        "metadata": {"instagram": {"type": "post", "shouldShareToFeed": True}}
    }
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
    resp = json.loads(result.stdout)
    if "errors" in resp:
        err = resp["errors"][0]
        if "RATE_LIMIT" in str(err):
            raise Exception("RATE_LIMITED")
        raise Exception(f"GraphQL error: {err['message']}")
    return resp

def upload_image(image_path):
    """Upload image to imgur, return public URL."""
    print(f"Uploading image: {image_path}")
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", "https://api.imgur.com/3/image",
         "-H", "Authorization: Client-ID 546c25a59c58ad7",
         "-F", f"image=@{image_path}"],
        capture_output=True, text=True, timeout=30
    )
    data = json.loads(result.stdout)
    link = data.get("data", {}).get("link")
    if not link:
        # Fallback to catbox
        print("Imgur failed, trying catbox.moe...")
        result = subprocess.run(
            ["curl", "-s", "-F", "reqtype=fileupload",
             "-F", f"fileToUpload=@{image_path}",
             "https://catbox.moe/user/api.php"],
            capture_output=True, text=True, timeout=30
        )
        link = result.stdout.strip()
        if not link.startswith("http"):
            raise Exception(f"Image upload failed: {result.stdout}")
    print(f"Image URL: {link}")
    return link

def create_post(channel_key, text, image_url):
    """Create a post on a single channel. Returns (success, detail_str)."""
    ch = CHANNELS[channel_key]
    
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
    
    variables = {
        "input": {
            "channelId": ch["id"],
            "text": text,
            "mode": "shareNow",
            "schedulingType": "automatic",
            "assets": {"images": [{"url": image_url}]} if image_url else {},
            "metadata": ch["metadata"]
        }
    }
    
    # Remove empty assets
    if not image_url:
        del variables["input"]["assets"]
    
    resp = gql(query, variables)
    cp = resp.get("data", {}).get("createPost", {})
    post = cp.get("post")
    msg = cp.get("message")
    
    if not post:
        return False, f"API error: {msg or json.dumps(cp)}"
    
    # Verify status after a few seconds
    time.sleep(5)
    check = gql('{ post(input: {id: "' + post['id'] + '"}) { status error { message rawError } } }')
    actual = check.get("data", {}).get("post", {})
    status = actual.get("status", "unknown")
    error = actual.get("error")
    
    if status == "sent":
        return True, f"Posted (id: {post['id']})"
    elif status == "sending":
        # Give it more time
        time.sleep(10)
        check2 = gql('{ post(input: {id: "' + post['id'] + '"}) { status error { message } } }')
        actual2 = check2.get("data", {}).get("post", {})
        status2 = actual2.get("status", "unknown")
        if status2 in ("sent", "sending"):
            return True, f"Posted (id: {post['id']}, status: {status2})"
        error2 = actual2.get("error")
        return False, f"Failed after wait (id: {post['id']}, status: {status2}, error: {error2})"
    elif error:
        return False, f"Error (id: {post['id']}): {error.get('message', '')} | {error.get('rawError', '')}"
    else:
        return False, f"Unknown status: {status} (id: {post['id']})"

def main():
    parser = argparse.ArgumentParser(description="Post to Buffer social channels")
    parser.add_argument("--text", required=True, help="Post text")
    parser.add_argument("--image", help="Path to image file (optional)")
    parser.add_argument("--image-url", help="Public URL of image (skip upload)")
    parser.add_argument("--channels", default="fb,li,ig", help="Comma-separated: fb,li,ig (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be posted without posting")
    args = parser.parse_args()
    
    channel_keys = [c.strip() for c in args.channels.split(",")]
    for k in channel_keys:
        if k not in CHANNELS:
            print(f"ERROR: Unknown channel '{k}'. Use: fb, li, ig")
            sys.exit(1)
    
    # Handle image
    image_url = args.image_url
    if args.image and not image_url:
        image_url = upload_image(args.image)
    
    if args.dry_run:
        print("\n=== DRY RUN ===")
        print(f"Text: {args.text[:100]}...")
        print(f"Image: {image_url or 'none'}")
        print(f"Channels: {', '.join(CHANNELS[k]['name'] for k in channel_keys)}")
        return
    
    # Post to each channel
    print(f"\nPosting to {len(channel_keys)} channel(s)...\n")
    results = {}
    for k in channel_keys:
        name = CHANNELS[k]["name"]
        try:
            success, detail = create_post(k, args.text, image_url)
            status = "✅" if success else "❌"
            results[name] = {"success": success, "detail": detail}
            print(f"  {status} {name}: {detail}")
        except Exception as e:
            results[name] = {"success": False, "detail": str(e)}
            print(f"  ❌ {name}: {e}")
        time.sleep(2)
    
    # Summary
    succeeded = sum(1 for r in results.values() if r["success"])
    print(f"\n{'='*40}")
    print(f"Results: {succeeded}/{len(results)} channels posted successfully")
    
    # Write results file
    with open("/tmp/buffer_post_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    sys.exit(0 if succeeded == len(results) else 1)

if __name__ == "__main__":
    main()
