# Active Directory Authentication & Nested Groups Pattern

## Context and Purpose
Pattern for authenticating and synchronizing users against Microsoft Active Directory using `ldap3`, specifically handling:
- Nested groups (groups inside groups, e.g. `IT` inside `RRHH` or `Comercial`).
- Multi-OU user distribution (users in different Organizational Units than the configured group).
- Multi-group configuration in environment variables (`AD_GROUP_NAME="RRHH, IT"` or `"Comercial, IT"`).

## Implementation Details (app/services/ad_auth.py)

### 1. Domain Root Search Scope (`_domain_root_dn`)
Extracts the `DC=...,DC=...` domain components from `AD_BASE_DN` or group DNs.
- **Why**: If `AD_BASE_DN` is scoped to a specific OU and users of sub-groups reside in another OU, LDAP subtree searches from a single OU fail to find them. Searching from domain root resolves all authorized users across any OU.

### 2. Recursive Subgroup Discovery (`_collect_nested_group_dns`)
Discovers nested groups using a breadth-first search (BFS) with cycle detection (`all_group_dns` set):
- **Direction A**: Search for groups with `(memberOf=<current_group_dn>)`.
- **Direction B**: Read the `member` attribute of the container group with `BASE` search scope, checking if any referenced DN is `(objectClass=group)`.

### 3. Hybrid Membership Filter (`_build_member_of_filter`)
Combines:
- Native AD chain evaluation: `(memberOf:1.2.840.113556.1.4.1941:=<root_group_dn>)`
- Explicit membership clauses for each discovered group: `(memberOf=<group_dn>)`
Filter format:
```ldap
(&
    (objectClass=user)
    (!(objectClass=computer))
    (|
        (memberOf:1.2.840.113556.1.4.1941:=<root_dn>)
        (memberOf=<dn_1>)
        (memberOf=<dn_2>)
    )
)
```

### 4. User Listing and Authentication
- `list_ad_group_users()`: Queries users matching the membership filter, deduplicates by lowercase username, and returns structured `ActiveDirectoryGroupUser` objects.
- `authenticate_ad_user(username, password)`: Searches user by `login_attr` with the membership filter under `domain_root_dn`, retrieves their DN, and performs a separate `SIMPLE` bind with the user credentials to validate the password.
