"""
Refresh le token Azure B2C et met a jour les variables Railway.
Execute par GitHub Actions toutes les 30 min depuis l'infrastructure
Microsoft (qui peut atteindre Azure B2C, contrairement a Railway).
"""

import os
import sys
import time

import requests

# Azure B2C
REFRESH_URL = (
    "https://france365B2C.b2clogin.com"
    "/france365B2C.onmicrosoft.com"
    "/B2C_1A_signup_signin"
    "/oauth2/v2.0/token"
)
CLIENT_ID = "cbba759f-45bc-4c21-bd77-533388735d6a"
SCOPE     = (
    "openid profile offline_access "
    "https://france365B2C.onmicrosoft.com"
    "/f86b75cc-7549-4e7b-9f20-c41117f94807/access_as_user"
)

# Railway GraphQL
RAILWAY_API = "https://backboard.railway.com/graphql/v2"


def refresh_b2c(refresh_tok: str) -> dict:
    print("[B2C] Refresh en cours...")
    resp = requests.post(
        REFRESH_URL,
        data={
            "grant_type":    "refresh_token",
            "client_id":     CLIENT_ID,
            "refresh_token": refresh_tok,
            "scope":         SCOPE,
        },
        headers={
            "Origin":     "https://mon-vie-via.businessfrance.fr",
            "Referer":    "https://mon-vie-via.businessfrance.fr/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/147.0.0.0 Safari/537.36",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[B2C] FAIL HTTP {resp.status_code}: {resp.text[:300]}")
        sys.exit(1)
    data = resp.json()
    print(f"[B2C] OK — token valide {data.get('expires_in')}s")
    return data


def gql(query: str, token: str, variables: dict = None) -> dict:
    resp = requests.post(
        RAILWAY_API,
        json={"query": query, "variables": variables or {}},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        },
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[RAILWAY] HTTP {resp.status_code}: {resp.text[:500]}")
        sys.exit(1)
    data = resp.json()
    if "errors" in data:
        print(f"[RAILWAY] GraphQL error: {data['errors']}")
        sys.exit(1)
    return data["data"]


def find_ids(railway_token: str) -> tuple[str, str, str]:
    """Trouve project/env/service IDs automatiquement."""
    query = """
    query {
      me {
        projects {
          edges {
            node {
              id
              name
              environments { edges { node { id name } } }
              services     { edges { node { id name } } }
            }
          }
        }
      }
    }
    """
    data = gql(query, railway_token)
    for p_edge in data["me"]["projects"]["edges"]:
        p = p_edge["node"]
        for s_edge in p["services"]["edges"]:
            s = s_edge["node"]
            if "vie" in s["name"].lower() or "alert" in s["name"].lower():
                envs = p["environments"]["edges"]
                env = next(
                    (e["node"] for e in envs if e["node"]["name"] == "production"),
                    envs[0]["node"],
                )
                print(f"[RAILWAY] Found project '{p['name']}' / service '{s['name']}'")
                return p["id"], env["id"], s["id"]
    print("[RAILWAY] Aucun service VIE trouve sur ton compte Railway")
    sys.exit(1)


def update_var(railway_token: str, project_id: str, env_id: str,
               service_id: str, name: str, value: str) -> None:
    mutation = """
    mutation upsert($input: VariableUpsertInput!) {
      variableUpsert(input: $input)
    }
    """
    gql(mutation, railway_token, {
        "input": {
            "projectId":     project_id,
            "environmentId": env_id,
            "serviceId":     service_id,
            "name":          name,
            "value":         value,
        }
    })
    print(f"[RAILWAY] {name} update OK")


def main():
    refresh_tok   = os.environ["REFRESH_TOKEN"]
    railway_token = os.environ["RAILWAY_TOKEN"]

    new = refresh_b2c(refresh_tok)
    access     = new["access_token"]
    refresh_n  = new.get("refresh_token", refresh_tok)
    expires_at = int(time.time()) + int(new.get("expires_in", 3600))

    project_id, env_id, service_id = find_ids(railway_token)

    update_var(railway_token, project_id, env_id, service_id, "ACCESS_TOKEN",     access)
    update_var(railway_token, project_id, env_id, service_id, "REFRESH_TOKEN",    refresh_n)
    update_var(railway_token, project_id, env_id, service_id, "TOKEN_EXPIRES_AT", str(expires_at))

    print(f"[OK] Termine — token valide jusqu'a {time.strftime('%H:%M:%S UTC', time.gmtime(expires_at))}")


if __name__ == "__main__":
    main()
