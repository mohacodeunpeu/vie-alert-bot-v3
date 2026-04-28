import os
import sys
import time
import requests

# ✅ FIX URL (minuscule)
REFRESH_URL = "https://france365b2c.b2clogin.com/france365b2c.onmicrosoft.com/B2C_1A_signup_signin/oauth2/v2.0/token"

CLIENT_ID = "cbba759f-45bc-4c21-bd77-533388735d6a"

# ✅ FIX SCOPE
SCOPE = "openid profile offline_access https://graph.microsoft.com/.default"

RAILWAY_API = "https://backboard.railway.app/graphql/v2"


def refresh_b2c(refresh_tok: str) -> dict:
    print("[B2C] Refresh en cours...")

    resp = requests.post(
        REFRESH_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "refresh_token": refresh_tok.strip(),  # sécurité
            "scope": SCOPE,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        timeout=30,
    )

    print("STATUS:", resp.status_code)

    if resp.status_code != 200:
        print(f"[B2C] FAIL: {resp.text}")
        sys.exit(1)

    data = resp.json()
    print("[B2C] SUCCESS")

    return data


def gql(query: str, token: str, variables: dict = None) -> dict:
    resp = requests.post(
        RAILWAY_API,
        json={"query": query, "variables": variables or {}},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if resp.status_code != 200:
        print(f"[RAILWAY] HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)

    data = resp.json()

    if "errors" in data:
        print(f"[RAILWAY] ERROR: {data['errors']}")
        sys.exit(1)

    return data["data"]


def find_ids(token: str):
    query = """
    query {
      me {
        projects {
          edges {
            node {
              id
              name
              environments { edges { node { id name } } }
              services { edges { node { id name } } }
            }
          }
        }
      }
    }
    """

    data = gql(query, token)

    for p in data["me"]["projects"]["edges"]:
        proj = p["node"]

        for s in proj["services"]["edges"]:
            srv = s["node"]

            if "vie" in srv["name"].lower():
                env = proj["environments"]["edges"][0]["node"]

                print(f"[RAILWAY] OK {proj['name']} / {srv['name']}")
                return proj["id"], env["id"], srv["id"]

    print("[RAILWAY] NOT FOUND")
    sys.exit(1)


def update(token, project, env, service, name, value):
    mutation = """
    mutation ($input: VariableUpsertInput!) {
      variableUpsert(input: $input)
    }
    """

    gql(mutation, token, {
        "input": {
            "projectId": project,
            "environmentId": env,
            "serviceId": service,
            "name": name,
            "value": value,
        }
    })

    print(f"[RAILWAY] {name} OK")


def main():
    refresh_tok = os.environ["REFRESH_TOKEN"]
    railway_tok = os.environ["RAILWAY_TOKEN"]

    data = refresh_b2c(refresh_tok)

    access = data["access_token"]
    refresh_new = data.get("refresh_token", refresh_tok)

    expires = int(time.time()) + int(data.get("expires_in", 3600))

    p, e, s = find_ids(railway_tok)

    update(railway_tok, p, e, s, "ACCESS_TOKEN", access)
    update(railway_tok, p, e, s, "REFRESH_TOKEN", refresh_new)
    update(railway_tok, p, e, s, "TOKEN_EXPIRES_AT", str(expires))

    print("✅ DONE")


if __name__ == "__main__":
    main()
