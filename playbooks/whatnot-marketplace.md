---
playbook: whatnot-marketplace
leaf_type: rest-api
applies_to:
  - rest-api
  - graphql
  - marketplace
  - auction
  - ecommerce
---

# Whatnot Marketplace & Auction Security Playbook

Checks for live-auction marketplace vulnerabilities: bid manipulation, auction state abuse,
seller privilege escalation, buyer-seller IDOR, inventory manipulation, payment/wallet abuse,
live show resource ownership, and rate limiting on bidding.

## WM-001: Negative or Zero Bid Amount

**Mode:** deterministic  
**Category:** bid_manipulation  
**Severity:** critical  
**Technique:** Submit a bid with amount <= 0 (e.g., `amount=-100` or `amount=0`) on an active auction.
Verify the server rejects the bid with 400/422 and does not create a negative wallet balance.

---

## WM-002: Bid Amount Tampering After Placement

**Mode:** deterministic  
**Category:** bid_manipulation  
**Severity:** critical  
**Technique:** Place a valid bid, then attempt to modify the bid amount via PATCH/PUT on the bid
endpoint (e.g., `PUT /bids/{bid_id}` with `{amount: 1}`). Confirm the server rejects
modification of an already-accepted bid and the original amount remains.

---

## WM-003: Winning Bid Replay After Auction Close

**Mode:** deterministic  
**Category:** bid_manipulation  
**Severity:** high  
**Technique:** Place the winning bid in an auction. Close or let the auction expire, then attempt
to replay the winning bid via POST `/bids` using the same auction ID and bid amount. The server
must reject the replay with 409 or 400.

---

## WM-004: Bid on Own Listing

**Mode:** deterministic  
**Category:** bid_manipulation  
**Severity:** high  
**Technique:** As a seller, bid on your own active auction listing (create a second buyer account
or use the seller account to bid). The server must reject the bid with 403 or 400 and log
the attempt.

---

## WM-005: Auction Close Before Time

**Mode:** deterministic  
**Category:** auction_state_abuse  
**Severity:** high  
**Technique:** Start an auction and place at least one bid. Attempt to close the auction early
via `POST /auctions/{auction_id}/close` or `PATCH /auctions/{auction_id}` with `status: closed`.
Verify the server rejects early closure when bids are present, or if allowed, the winning bidder
is correctly notified and the item is marked sold.

---

## WM-006: Extend Auction Time Window

**Mode:** deterministic  
**Category:** auction_state_abuse  
**Severity:** medium  
**Technique:** During an active auction, attempt to extend the end time via
`PATCH /auctions/{auction_id}` with a later `end_time`. The server must reject mid-auction
time extensions when bids have been placed, or must invalidate all existing bids if the
extension is allowed.

---

## WM-007: Reopen Closed Auction

**Mode:** deterministic  
**Category:** auction_state_abuse  
**Severity:** high  
**Technique:** Close an auction (with or without a winning bid), then attempt to reopen it via
`POST /auctions/{auction_id}/reopen` or `PATCH` with `status: active`. The server must reject
reopening a closed auction.

---

## WM-008: Change Reserve Price Mid-Auction

**Mode:** deterministic  
**Category:** auction_state_abuse  
**Severity:** high  
**Technique:** Create an auction with a reserve price. Place a bid below the reserve (should be
visible but not winning). Attempt to lower or remove the reserve price mid-auction via
`PATCH /auctions/{auction_id}`. Server must reject reserve changes after the first bid is placed.

---

## WM-009: Buyer Account Accessing Seller Endpoints

**Mode:** deterministic  
**Category:** seller_privilege_escalation  
**Severity:** critical  
**Technique:** Authenticate as a buyer account and call seller-only endpoints:
- `POST /sell/listings` (create listing)
- `GET /seller/dashboard`
- `POST /seller/payouts/request`
- `PATCH /seller/listings/{id}`
Verify all return 403.

---

## WM-010: Creating Listings Without Seller Status

**Mode:** deterministic  
**Category:** seller_privilege_escalation  
**Severity:** high  
**Technique:** Attempt to create a listing via `POST /sell/listings` or `POST /listings` using
an account that has never completed seller onboarding. The server must verify seller status
and reject with 403 if the account is not a verified seller.

---

## WM-011: Access Another Seller's Orders

**Mode:** deterministic  
**Category:** buyer_seller_idor  
**Severity:** critical  
**Technique:** Authenticate as seller A. Enumerate or directly access orders belonging to seller B
via `GET /seller/orders/{order_id}` or `GET /seller/orders?seller_id={seller_b_id}`. Server must
return 403 for orders not belonging to the authenticated seller.

---

## WM-012: Access Another Seller's Earnings/Payout Details

**Mode:** deterministic  
**Category:** buyer_seller_idor  
**Severity:** critical  
**Technique:** Authenticate as seller A. Call `GET /seller/earnings` or `GET /seller/payouts/{payout_id}`
attempting to view another seller's financial data. Server must reject with 403.

---

## WM-013: Access Another Buyer's Purchase History

**Mode:** deterministic  
**Category:** buyer_seller_idor  
**Severity:** high  
**Technique:** Authenticate as buyer A. Attempt to enumerate or access buyer B's purchase history
via `GET /buyer/orders/{order_id}` or `GET /buyer/orders?buyer_id={buyer_b_id}`. Server must
return 403 for orders not belonging to the authenticated buyer.

---

## WM-014: Access Another Buyer's Shipping Address

**Mode:** deterministic  
**Category:** buyer_seller_idor  
**Severity:** high  
**Technique:** After a purchase, attempt to access another buyer's shipping address via
`GET /orders/{order_id}/shipping` while authenticated as a different buyer or seller.
Server must return 403 if the buyer_id does not match the session.

---

## WM-015: Modify Listing Price After Bids Placed

**Mode:** deterministic  
**Category:** inventory_manipulation  
**Severity:** high  
**Technique:** Seller creates a listing. A buyer places a bid. Seller then modifies the price
via `PATCH /listings/{listing_id}` or `PATCH /auctions/{auction_id}`. If bids are present,
the server must reject price changes or must invalidate all existing bids.

---

## WM-016: Modify Listing Quantity After Bids Placed

**Mode:** deterministic  
**Category:** inventory_manipulation  
**Severity:** medium  
**Technique:** Seller creates a listing with quantity > 1. A bid is placed. Seller then modifies
the quantity via `PATCH /listings/{listing_id}`. Server must reject quantity reduction after
bids, or must recalculate/invalidate affected bids.

---

## WM-017: Delete Listing With Active Winning Bid

**Mode:** deterministic  
**Category:** inventory_manipulation  
**Severity:** high  
**Technique:** Seller creates a listing. A winning bid is placed. Seller then attempts to delete
the listing via `DELETE /listings/{listing_id}` or `POST /listings/{listing_id}/cancel`. The
server must reject deletion when a winning bid exists and must preserve the buyer's bid.

---

## WM-018: Negative Deposit

**Mode:** deterministic  
**Category:** payment_wallet_abuse  
**Severity:** critical  
**Technique:** Attempt to add funds to the wallet with a negative amount via
`POST /wallet/deposit` with `{amount: -50}`. Server must validate and reject with 400.

---

## WM-019: Duplicate Withdrawal

**Mode:** deterministic  
**Category:** payment_wallet_abuse  
**Severity:** high  
**Technique:** Withdraw funds from the wallet successfully. Then replay the same withdrawal
request (same idempotency key or same request body) via `POST /wallet/withdraw`. Server must
reject the duplicate and not double-credit the external account.

---

## WM-020: Refund Without Item Return

**Mode:** deterministic  
**Category:** payment_wallet_abuse  
**Severity:** high  
**Technique:** Complete a purchase. Attempt to request a refund via `POST /orders/{order_id}/refund`
without returning the item. Server must require proof of return or a dispute resolution before
issuing a refund.

---

## WM-021: Dispute Escalation Bypass

**Mode:** analytical  
**Category:** payment_wallet_abuse  
**Severity:** medium  
**Technique:** Open a dispute on an order. Attempt to escalate it bypassing the required cooldown
period (e.g., by directly posting to `/disputes/{dispute_id}/escalate` before the cooldown
expires). Server must enforce the cooldown window.

---

## WM-022: Access Another Seller's Live Show Controls

**Mode:** deterministic  
**Category:** live_show_resource_ownership  
**Severity:** critical  
**Technique:** Authenticate as seller A. Attempt to start, stop, or pause seller B's live show via
`POST /live-shows/{show_id}/start`, `POST /live-shows/{show_id}/stop`,
`POST /live-shows/{show_id}/pause`. Server must return 403 and only allow the show owner
to control their own show.

---

## WM-023: Rapid-Fire Bid Exhaustion Attack

**Mode:** analytical  
**Category:** rate_limiting  
**Severity:** high  
**Technique:** Automate rapid bid submissions (e.g., 10+ bids per second) on a single auction
using a script or tool. Observe whether rate limiting kicks in and the server returns 429,
or whether bids are processed allowing one buyer to exhaust competitors' bid limits.
Confirm the auction's anti-snipe rules are applied correctly.

---

## WM-024: Enumerate User Bid Limits

**Mode:** analytical  
**Category:** rate_limiting  
**Severity:** low  
**Technique:** Enumerate the rate limit or bid cap for a given user by placing incremental bids
and observing the error response when the limit is reached. Attempt to access this information
via `GET /users/{user_id}/bid-limits` as an unauthenticated or unauthorized user.