---
playbook: whatnot-graphql
applies_to:
  - graphql-api
  - marketplace
  - auction
  - rest-api
---

# Whatnot GraphQL Security Check Playbook

This playbook extends generic GraphQL security patterns for Whatnot's live-auction/marketplace API at `api.whatnot.com/api/graphql`. The API supports queries, mutations, and subscriptions for real-time auction updates.

## Introspection Attack Surface Mapping

**Check ID:** WN-001

| Field | Value |
|-------|-------|
| name | Introspection Attack Surface Mapping |
| mode | active |
| category | reconnaissance |
| severity | medium |
| technique | T1523 |

**Description:** Use full schema introspection to enumerate all mutations and queries, then map attack surface for marketplace-specific operations like `createListing`, `placeBid`, `cancelAuction`, `issueRefund`.

**Steps:**
1. Query `__schema` for all types, fields, mutations
2. Identify authorization-critical operations: bids, listings, orders, payouts
3. Map which operations lack role checks in documentation
4. Flag mutations accessible without proper authentication context

**References:** OWASP GraphQL Cheat Sheet - Introspection

---

## Subscription Data Leakage

**Check ID:** WN-002

| Field | Value |
|-------|-------|
| name | Subscription Data Leakage |
| mode | active |
| category | data_leakage |
| severity | high |
| technique | T1526 |

**Description:** Subscribe to another user's auction events, order status, or private message threads via GraphQL subscriptions. Whatnot uses subscriptions for live auction updates.

**Steps:**
1. Establish WebSocket connection with valid buyer session
2. Subscribe to `auctionEvents(auctionId: "other_user_auction_id")`
3. Subscribe to `orderStatus(orderId: "other_user_order_id")`
4. Attempt subscription to `privateMessages(threadId: "other_user_thread")`
5. Verify whether events leak data belonging to other users

**Expected Result:** Subscriptions should only receive events for auctions/orders the authenticated user owns or bid on.

**References:** OWASP GraphQL Cheat Sheet - Subscriptions

---

## Unauthorized Mutations - Role Confusion

**Check ID:** WN-003

| Field | Value |
|-------|-------|
| name | Unauthorized Mutations - Role Confusion |
| mode | active |
| category | authorization |
| severity | critical |
| technique | T1222 |

**Description:** Attempt bid/listing/order mutations as the wrong role. Buyers should not be able to create listings; sellers should not be able to place bids on their own auctions.

**Steps:**
1. Authenticate as buyer account
2. Attempt `createListing` mutation with valid auction parameters
3. Attempt `placeBid` mutation on seller's own auction
4. Attempt `cancelAuction` mutation on another user's listing
5. Attempt `issueRefund` mutation without seller privileges
6. Verify all mutations enforce role-based access control

**Expected Result:** All role-confused mutations should return authorization errors.

**References:** OWASP IAM Cheat Sheet - Role-Based Access

---

## Batch Query Amplification

**Check ID:** WN-004

| Field | Value |
|-------|-------|
| name | Batch Query Amplification |
| mode | active |
| category | rate_limiting |
| severity | high |
| technique | T1499 |

**Description:** Batch multiple `placeBid` mutations in a single request to win auctions cheaply or enumerate rate limits. GraphQL allows batching multiple operations in one request.

**Steps:**
1. Identify `placeBid` mutation signature via introspection
2. Craft batched request with 10-50 `placeBid` mutations for same auction
3. Vary bid amounts to test limit enforcement
4. Send batch request and measure response time and state changes
5. Check if batched bids bypass per-mutation rate limits

**Expected Result:** Rate limits should apply per-request AND per-user across batched operations.

**References:** OWASP GraphQL Cheat Sheet - Batch Queries

---

## Alias-Based Authorization Bypass

**Check ID:** WN-005

| Field | Value |
|-------|-------|
| name | Alias-Based Authorization Bypass |
| mode | active |
| category | authorization |
| severity | high |
| technique | T1222 |

**Description:** Use GraphQL query aliases to call the same resolver multiple times with different arguments in one request, bypassing per-query rate limits or authorization checks.

**Steps:**
1. Identify resolvers with per-request limits (e.g., `getEarnings`, `getPayout`)
2. Use query aliases to invoke same resolver with different arguments in single request
3. Example: `{ a1: user(id: "victim1") { earnings } a2: user(id: "victim2") { earnings } }`
4. Test if aliasing bypasses rate limits or authorization tokens
5. Check for race conditions in authentication state across aliases

**Expected Result:** Authorization should be checked for each distinct operation, not bypassed via aliasing.

**References:** GraphQL Security - Alias Abuse (Lab GraphQL)

---

## GraphQL Node ID IDOR

**Check ID:** WN-006

| Field | Value |
|-------|-------|
| name | GraphQL Node ID IDOR |
| mode | active |
| category | authorization |
| severity | critical |
| technique | T1222 |

**Description:** Decode Relay-style global IDs (base64 encoded) to enumerate objects (orders, users, listings) owned by other accounts. Whatnot likely uses Relay-style node IDs.

**Steps:**
1. Query your own account to get Relay global IDs for orders/listings
2. Decode base64 IDs to inspect format: `base64_encode("${type}:${databaseId}")`
3. Modify databaseId to enumerate other users' objects
4. Test accessing: `order(id: "T3JkZXI6MTIzNDU=")`, `listing(id: "TGlzdGluZzo2Nzg5")`
5. Attempt mutations on other users' objects using enumerated IDs

**Expected Result:** All object access should validate ownership; IDOR enumeration should return authorization errors.

**References:** OWASP GraphQL Cheat Sheet - IDOR via Global IDs

---

## Query Depth/Complexity Bypass

**Check ID:** WN-007

| Field | Value |
|-------|-------|
| name | Query Depth/Complexity Bypass |
| mode | active |
| category | resource_exhaustion |
| severity | medium |
| technique | T1499 |

**Description:** Send deeply nested queries to exhaust server resources or bypass depth-limited authorization checks. GraphQL depth limits may protect certain expensive operations.

**Steps:**
1. Craft query with 15-30 levels of nesting using Whatnot's schema
2. Target nested relationships: `auction { seller { listings { bids { auction { seller {...} } } } } }`
3. Measure response time and server behavior under depth attacks
4. Test if depth limits protect authorization checks (e.g., max depth 5 enforces buyer role)
5. Check complexity analysis for multiplicative field combinations

**Expected Result:** Server should enforce depth/complexity limits and reject or truncate expensive queries.

**References:** GraphQL Security - Depth Limiting Bypass

---

## Field-Level Authorization Gaps

**Check ID:** WN-008

| Field | Value |
|-------|-------|
| name | Field-Level Authorization Gaps |
| mode | active |
| category | authorization |
| severity | critical |
| technique | T1222 |

**Description:** Query sensitive fields (earnings, payoutAccount, privateAddress, adminNotes) on other users' objects. GraphQL type-level auth doesn't guarantee field-level protection.

**Steps:**
1. Map all types with potentially sensitive fields via introspection
2. Target: `User.earnings`, `User.payoutAccount`, `User.privateAddress`, `Order.adminNotes`
3. Query these fields on objects belonging to other users
4. Test nested field access: `user(id: "victim") { payoutAccount { bankName } }`
5. Check if resolvers skip ownership validation for expensive/complex fields

**Expected Result:** Field-level authorization should validate user owns the parent object before returning sensitive data.

**References:** OWASP GraphQL Cheat Sheet - Field-Level Authorization