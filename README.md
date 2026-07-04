# DTL — Dyadic Typed Layer

**A specification for typed, directed, controller-confirmed relationships between agents.**

| | |
|---|---|
| **Version** | 0.5 (draft / v0) |
| **Status** | Draft (v0) |
| **Author** | Evan Phelan (Minuet Labs) |
| **License** | CC-BY 4.0 |
| **Date** | 2026-07-04 |

*DTL is unrelated to DTLS (Datagram Transport Layer Security).*

---

## Abstract

DTL (Dyadic Typed Layer) defines a single, minimal primitive: a **typed, directed relationship between two agents that the controller of each agent has confirmed**, together with that relationship's five-state lifecycle: `proposed`, `established`, `declined`, `withdrawn` (a proposal retracted before confirmation), `revoked` (an established relationship terminated). The name describes the primitive — *Dyadic* (it concerns one pair of parties), *Typed* (the relationship carries exactly one kind), *Layer* (it sits above an identity substrate, not inside it).

Agent ecosystems have built out several coordination layers — **identity** (who an agent is), **reputation and attestation** (what is asserted about an agent), and **discovery and messaging** (how agents find and talk to each other). One primitive is comparatively underserved — the **relationship**: a standing, acknowledged, directed connection between two specific agents, recording *that* they are related and *in what capacity*. No existing standard, to the author's knowledge, provides exactly this primitive in this form (§9). DTL specifies it and nothing more. It is normative about the mechanism (a typed, directed, two-party, controller-confirmed edge and its lifecycle) and deliberately silent about substrate, transport, storage, and the open vocabulary of relationship types. DTL records relationships; it does not enforce them — whether a relationship grants any capability is the consuming system's decision (§8). An informative binding to ERC-8004 is provided as the first anchoring substrate.

---

## 1. Motivation

Autonomous software agents increasingly act on behalf of different principals and across organizational boundaries. Several coordination layers are now actively addressed:

- **Identity** — stable, verifiable identifiers for agents (registries, DIDs, on-chain agent records).
- **Reputation / attestation** — assertions *about* an agent: scores, reviews, verifiable credentials, trust signals.
- **Discovery and messaging** — how agents are found and how they exchange messages (e.g. agent-interaction protocols).

Identity and attestation are **one-way**: one party makes a claim about, or an identifier for, another. Discovery and messaging concern *communication*, not a standing bond. None captures a **relationship** — a connection between two *specific* agents that *both* sides acknowledge, in a *specific* capacity, with a *direction*: "agent A delegates to agent B," "agent A may message agent B," "agent A depends on agent B."

The constructs closest to this are either one-way (attestations, reputation, and recent verifiable-delegation schemes) or relationship-shaped but not typed for the *standing* relationship (peer connections that record *that* two parties are connected, where any type present describes the connecting handshake rather than the kind of standing relationship that results). The gap is a connection that is at once **acknowledged by both parties**, **directed**, **typed**, and **lifecycle-bearing**.

This is a small but load-bearing unit of coordination. Google DeepMind's June 2026 multi-agent-safety funding call highlighted identity, reputation, and commitment among the priorities for secure cross-platform agent interactions — the same problem space DTL addresses. "Commitment" is used here in the broad sense of a standing, acknowledged relationship — **not** the narrower game-theoretic sense of a *commitment device* that binds an agent's future choices (as studied in the cooperative-AI literature on decentralized commitment devices). DTL specifies the smallest useful version of a standing relationship: **one** confirmed, typed, directed relationship between **two** agents.

### 1.1 Scope and Non-Goals

**In scope.** The single pairwise relationship — its record, its one type, its lifecycle, and the semantics of confirmation. This is the *dyad*: exactly two parties.

**Out of scope.**

- The **network or graph** that emerges from many relationships. DTL defines the edge; it specifies no global query, ranking, traversal, or discovery semantics over a collection of edges.
- **Transport and storage.** Where records live and how they are exchanged is a deployment concern.
- **Identity issuance.** DTL assumes each agent already has a stable identifier on some substrate; minting that identifier is the substrate's job.
- **Reputation, scoring, and capability enforcement.** A relationship records *consent to a relationship*, not trustworthiness, and it grants or constrains no capability (see §8).
- **Proof mechanics and conflict resolution.** The canonical serialization of a record, the exact signing input and verification procedure for the `signed` profile, and the resolution of conflicting or concurrent actions (e.g. a total order across replicas) are **binding- and deployment-defined**, not specified here, and are a known area for a future version. A *binding* (§7) supplies the concrete, interoperable profile against which independent implementations interoperate.

**General in mechanism, specific in framing.** The mechanism is defined over generic *parties that have a controller*; this specification frames and motivates it around **AI agents as the primary case**. A DTL agent may be software or embodied (e.g. robotics); DTL operates above the agent's internal cognitive architecture and embodiment, and makes no assumption about how an agent is built. The following are deliberately left as **non-goals for v1**, noted only for forward compatibility — the mechanism admits them, but they are not specified here:

- **(a) Non-agent parties.** The same edge admits human↔agent (an agent and its principal) and agent↔service relationships. Agents are the primary case; these are not specified.
- **(b) Cross-substrate relationships.** Because confirmation is performed independently by each party's controller (§6), two agents anchored on *different* substrates could in principle confirm one relationship. This interoperability case is enabled in principle but not specified.

---

## 2. Terminology

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119 and RFC 8174 when, and only when, they appear in capitals.

- **Agent** — an autonomous actor with a stable identity on some substrate. An agent may be software or embodied (§1.1); DTL makes no assumption about its internal construction. Agents are the endpoints of a relationship.
- **Controller** — the authority recognized by an agent's identity substrate as able to authorize actions on the agent's behalf. A controller **MAY** be a human owner, a delegated organization, or the agent itself. (The term echoes *controller* in W3C Decentralized Identifiers; in DTL it denotes the authorization authority for an agent, which **MAY** but need not coincide with the controller of any DID document.)
- **Party** — one of the two agents in a relationship. Each party has a controller.
- **Relationship** — a typed, directed connection from a **source** agent to a **target** agent, as defined by this specification.
- **Relationship record** — the data structure representing a relationship and its current state.
- **Proof of authorization** — evidence that a party's controller authorized a relationship action (proposal, confirmation, decline, withdrawal, or revocation). Its concrete form is determined by the confirmation profile.
- **Confirmation profile** — a named scheme that defines how a proof of authorization is produced and verified, and the degree of trust it conveys.

---

## 3. The Relationship Record

A relationship is represented by a **relationship record**. A record **MUST** contain:

- **`source`** — the identifier of the source agent (substrate-defined).
- **`target`** — the identifier of the target agent (substrate-defined). `target` **MUST NOT** equal `source` (no self-relationship).
- **`type`** — exactly one relationship type, a non-empty string drawn from an open vocabulary (§4).
- **`status`** — the lifecycle state (§5): one of `proposed`, `established`, `declined`, `withdrawn`, `revoked`.
- **`proofs`** — the proofs of authorization for the lifecycle actions taken so far, in the form defined by the profile. A record **MUST** carry one proof for each action that brought it to its current `status` (§6); Appendix A specifies the required entries per state.
- **`profile`** — the confirmation profile (§6) under which its proofs were produced.

A record **MAY** carry an `id`, timestamps (`created_at`, `updated_at`), a free-form human-readable `description`, and an `ext` object holding deployment- or substrate-specific extension fields. The record's top-level fields are otherwise closed (Appendix A); `ext` is the single designated place for fields this specification does not define, and its contents are unconstrained.

A relationship is **directed**: `source → target` is significant and is not symmetric. "A `delegates_to` B" is a different relationship from "B `delegates_to` A." A verifier **MUST NOT** treat a relationship as symmetric.

The constraint that `source` and `target` **MUST** differ (no self-relationship) is normative but is **not expressible in JSON Schema** — Draft 2020-12 cannot compare two instance values to each other. Implementations **MUST** enforce it outside the schema.

A normative JSON Schema for the record is given in Appendix A.

---

## 4. Types

A relationship **MUST** carry exactly one `type`.

The `type` vocabulary is **open**: `type` is a free-form string, and implementations **MAY** define their own types. This specification is normative about **typed-ness** (a relationship carries exactly one type) but **NOT** about the set of legal type *values*. A `type` is a **descriptive label** on the record: it names *what the relationship asserts* and is **not prescriptive** — this specification attaches **no behavioral semantics** to any type, and a type by itself grants no capability and triggers no enforcement (§8). It is a label, not a directive.

**Recommended vocabulary (informative).** Implementations are encouraged, for interoperability, to use the following bare identifiers where they apply:

- **`delegates_to`** — the source may request the target to perform work on its behalf.
- **`can_send_message_to`** — the source may send messages to the target.
- **`depends_on`** — the source depends on the target (e.g. for sequencing or a required input).

**Namespacing (SHOULD).** To avoid collisions in the open vocabulary: bare identifiers are reserved for types defined by this specification (the recommended vocabulary above). Any other type **SHOULD** be namespaced as a URI — for example `https://example.com/dtl/audits` — following the convention RFC 8288 (Web Linking) uses for extension relation types, which are themselves URIs.

---

## 5. Lifecycle

A relationship moves through the following states:

```
                       confirm
     proposed ──────────────────────────▶ established
        │  │                                   │
        │  │ withdraw                          │ revoke
        │  │ (source)                          │ (either party)
        │  ▼                                   ▼
        │  withdrawn (terminal)             revoked (terminal)
        │
        │ decline (target)
        ▼
     declined (terminal)
```

- A relationship is created by the **source's controller** in state **`proposed`**.
- While the relationship is **`proposed`**, the **target's controller** either **confirms** it (→ **`established`**) or **declines** it (→ **`declined`**); independently, the **source's controller** **MAY withdraw** its own still-unconfirmed proposal (→ **`withdrawn`**).
- An **`established`** relationship **MAY** be **revoked** (→ **`revoked`**) by *either* party's controller.
- **`withdrawn`**, **`declined`**, and **`revoked`** are **terminal**. A new relationship between the same parties **MAY** be proposed afresh.

A single principle governs every exit: **a controller may unilaterally retract its own authorization at any nonterminal stage in which it still holds that authorization; the change takes effect immediately and is attributable to that controller.** Before confirmation only the source has authorized, so only the source can unwind the proposal (**withdraw**), while the target unwinds simply by **declining** rather than confirming. After confirmation both parties have authorized, so *either* may unwind (**revoke**). Forming a relationship requires both sides; **exiting** one never does — requiring mutual consent to end a relationship would let one party trap the other in a stale edge.

**Multiplicity (deployment-defined).** This specification defines the lifecycle of a *single* relationship record. Whether two parties may simultaneously hold several relationships of the same `type`, and whether proposing afresh supersedes a terminal prior record or coexists with it, are **deployment-defined** and out of scope.

---

## 6. Confirmation Semantics

The defining property of DTL is **confirmation by both parties**: a relationship reaches **`established`** only when the controller of *each* party has authorized it — the **source** by proposing, the **target** by confirming. This two-party authorization is exactly what distinguishes a relationship from a one-way attestation. These are two **endpoint-role** authorizations — one for the source role, one for the target. DTL does not require the two controllers to be distinct; where a single controller holds both agents it authorizes both roles. The structural distinction DTL draws is two endpoint-role authorizations, not necessarily two independent parties.

Each authorization is a **proof of authorization**. What counts as a valid proof, and who can verify it, is set by the **confirmation profile** in force for the record. This specification defines two profiles and permits others.

The `proofs` of a record form an **append-only** set of authorizations — at most one per action, accrued as the record advances and never rewritten: a record **MUST** carry a proof of authorization for every lifecycle action (§5) that has brought it to its current `status`. A `proposed` record carries a `proposal` proof; an `established` record carries `proposal` and `confirmation`; a `declined` record carries `proposal` and `decline`; a `withdrawn` record carries `proposal` and `withdrawal`; and a `revoked` record carries `proposal`, `confirmation`, and `revocation`. Appendix A encodes these per-status requirements normatively — but constrains only *which* proofs are present, **not their contents**: the internal structure of each proof is profile-defined, so schema-validity does **not** imply proof-satisfaction. Like the `source` ≠ `target` constraint (§3), **proof attribution** — that a proof was genuinely produced by the named controller — is not expressible in JSON Schema and is the responsibility of the profile and the verifier.

- **`attested` profile.** A trusted third party (an *attesting service*) records that each controller authorized the relevant action. Verifiers trust the attesting service's record. This profile is convenient and requires no controller-held verification material, but a proof is **not independently verifiable** by a party that does not trust the attesting service, and typically not offline. Where an attested proof carries a `method` field (e.g. `siwe`, as in Appendix B.1), that field describes the *attester's* authentication process only; it confers no independent verifiability, and only the `signed` profile yields proofs a third party can check without trusting the attesting service. (Example: each controller authenticates to a platform, and the platform records the authorization.)
- **`signed` profile.** Each controller produces a proof that *any* party can verify **without relying on a trusted attesting service** — for example a digital signature over the record, verifiable against the controller's own published verification material. Verification still depends on *obtaining* that verification material — which may itself involve a resolver, DNS, or a ledger (a trust anchor of its own) — but not on a third party's attestation of the authorization. Whether verification can *also* be done **offline** depends on how the material is obtained — immediate for self-describing identifiers (e.g. `did:key`), but requiring a lookup for methods that resolve material over the network or a ledger (e.g. `did:web`, on-chain keys). Its integrity rests on the controller's verification material rather than on a trusted service.

A record **MUST** declare which profile produced its proofs. Profiles are extensible: a deployment **MAY** define additional profiles, provided each specifies how proofs are produced and verified and what trust they convey.

**Profiles vs bindings.** The two profiles defined here are trust *categories*, not wire-complete schemes — they classify the trust a proof conveys but do not by themselves fix a proof's contents, its canonical signing input, or a verification procedure. A concrete, *interoperable* profile — one against which two independent implementations can produce and check the same proofs — is supplied by a **binding** to a specific substrate (the ERC-8004 binding of §7 is the first). Canonicalization, signing input, and the verification procedure are therefore binding- and deployment-defined (a non-goal for v0; see §1.1).

**Field casing (informative).** Fields *defined by this specification* — record-level fields and the fields of the `attested` profile's proofs — use `snake_case` (e.g. `created_at`, `attested_by`). Fields adopted from an external standard inside a `proofs` object retain that standard's convention — for example `verificationMethod` keeps the camelCase form specified by W3C DID.

> **Autonomy (informative).** In the `signed` profile the controller that produces a proof **MAY** be the agent itself, when the agent holds its own verification material. This is the path by which a relationship can be formed with no human in the loop — the mechanism is neutral as to whether a controller is a human, an organization, or the agent itself.

---

## 7. Binding: ERC-8004 (Informative)

This binding describes how DTL maps onto ERC-8004 ("Trustless Agents"), the first substrate on which it is anchored. It is **informative**; nothing here is normative for DTL.

- **Identity / agents.** ERC-8004 provides on-chain agent identity on EVM chains. An agent's DTL identifier is its ERC-8004 agent identity, expressed as `chainId:agentId` (e.g. `11155111:123`) for unambiguous cross-chain reference.
- **Controller.** A party's controller is the agent's **on-chain owner** — the address recorded as the agent's owner on ERC-8004.
- **Confirmation (profile).** The reference deployment implements the **`attested`** profile: each controller authenticates with Sign-In with Ethereum (SIWE), the target confirms through a single-use confirmation link, and the service records both authorizations. A `signed` profile — direct signatures by each owner over the record — is the natural trustless extension and is not yet implemented.
- **Records are off-chain.** DTL relationship records are held off-chain, keyed to on-chain ERC-8004 identities; ERC-8004 supplies identity, DTL supplies the relationship layer above it.
- **Lifecycle mapping.** The reference implementation's statuses map to DTL states as follows: `verified` → **`established`**; `rejected` → **`declined`**; `proposed` and `pending` (proposal initiated, awaiting the target) → **`proposed`**. The implementation additionally has an `inferred` seeding state for *candidate* relationships that carry **no controller authorization**; these fall **outside** the DTL lifecycle and are not DTL relationships until proposed and confirmed. DTL's **`withdrawn`** and **`revoked`** states are defined by this specification but are **not yet implemented** in the reference deployment.
- **Type provenance.** The reference deployment uses five types: the recommended trio (`delegates_to`, `can_send_message_to`, `depends_on`) plus `supervises` and `complements`. The latter two are lower-confidence (`supervises` is awkward across organizational boundaries; `complements` is the least precisely observable) and are **not** part of the recommended vocabulary in §4. Note also that `complements` reads as *symmetric*, whereas DTL records are directed (§3); a mutual "complements" relationship is therefore represented as **two** explicit directed records, not one.

---

## 8. Security and Trust Considerations

- **Trust follows the profile.** The trust conveyed by an `established` relationship depends entirely on its confirmation profile. An `attested` relationship is only as trustworthy as its attesting service and is not portable to parties that do not trust that service; a `signed` relationship can be verified without trusting an attesting service, though still contingent on obtaining and trusting the controllers' verification material (and the resolver, DNS, or ledger through which it is published).
- **Controller compromise.** Whoever can act as a controller can authorize relationships for that agent. Compromise of a controller's credentials or keys permits forged proposals, confirmations, withdrawals, or revocations. Revocation limits the lifetime of a standing relationship but does not undo actions taken while it was `established`, and it constrains that lifetime only to the extent a verifier can observe current state — a stale or cached record may not yet reflect a revocation that has occurred.
- **Consent, not capability.** A relationship records that two controllers consented to a typed, directed connection. It does **not** by itself grant, constrain, or enforce any capability. A `delegates_to` relationship does not confer permission; enforcement is the responsibility of the systems that act on the relationship and is out of scope.
- **Replay and binding.** A proof of authorization **SHOULD** be bound to the specific relationship *instance* it authorizes — at minimum the fields that constitute the authorized proposition (`source`, `target`, `type`) and, where a deployment permits more than one record for the same `source`/`target`/`type` over time (§5), a value that distinguishes the specific record instance (such as its `id` or a per-proof nonce). Where such multiplicity is permitted, binding to the instance is **REQUIRED**, so that an old proof from a since-terminated relationship cannot be replayed onto a fresh proposal of the same triple; otherwise it **SHOULD** be present.
- **Direction integrity.** Because relationships are directed and asymmetric, verifiers **MUST** preserve `source`/`target` ordering and **MUST NOT** infer the reverse relationship from a record.
- **Proposal is not assent.** A `proposed` record carries only the *source's* authorization; a verifier **MUST NOT** read it as the target's agreement. Until confirmation it is an unaccepted offer, and a deployment **SHOULD** guard against unsolicited-proposal ("proposal spam") abuse.
- **Acknowledged, not solved (v0).** Several hardening concerns are deliberately deferred to bindings and future versions (see Non-Goals, §1.1): the canonical signing input and verification procedure for the `signed` profile; **controller rotation** (a relationship authorized under a key or owner that later changes); **domain separation** (ensuring a proof minted for one purpose, type, or deployment cannot be reinterpreted in another); and **freshness / stale state** (a verifier acting on an out-of-date record). DTL specifies the relationship and its lifecycle; closing these is binding- and deployment-specific work.

---

## 9. Related Work (Informative)

No existing standard, to the author's knowledge, provides exactly DTL's primitive — a relationship that is at once **typed on the standing relationship**, **directed**, **two-party (controller-confirmed)**, and **lifecycle-bearing**. The claim is **combinational**: each property below exists in prior art, but no single neighbor combines all four for an *open-vocabulary* standing relationship. The table summarizes where the closest neighbors sit; the notes give the detail.

| Prior art | Typed (on standing relationship) | Directed | Two-party confirmed | Lifecycle |
|---|---|---|---|---|
| DIDComm / DID Exchange connections | no (types the handshake) | yes | yes | yes |
| Verifiable delegation (AIP, LDP) | partial (delegation only) | yes | no (one-way grant) | no (no standing-relationship lifecycle) |
| One-way attestation (Verifiable Credentials, ERC-8240) | yes | yes | no | no |
| Labeled-edge models (RDF, FOAF, schema.org, XFN) | yes | yes | no | no |
| FIPA Contract Net | no (types the task) | yes | per task | per interaction |
| Commitment machines (Yolum & Singh) | partial (types the obligation) | yes | yes | yes |
| ActivityPub (`Follow` / `Accept` / `Undo`) | no (single fixed kind) | yes | yes | partial |
| XMPP presence subscriptions (RFC 6121) | no (single fixed kind) | yes | yes | yes |
| Social friend-graphs (proprietary) | no (single fixed kind) | varies | yes | partial |
| WS-Agreement (Open Grid Forum) | partial (agreement terms) | yes | yes | yes |
| **DTL** | **yes (open vocabulary)** | **yes** | **yes** | **yes** |

- **DIDComm / DID Exchange connections** (DID/SSI ecosystem) — the closest relationship-shaped prior art: a connection is mutually acknowledged, directed at setup, persistent, and lifecycle-bearing. A connection *can* carry a type — *DID Exchange Protocol 1.0* (Aries RFC 0023) and *Goal Codes* (RFC 0519) express a `goal` / `goal_code` — but that type describes the **purpose of the connecting handshake**, not the kind of the **standing relationship** it produces. DTL's contribution relative to this is a type on the *standing relationship itself*.
  *Worked example.* Suppose A and B establish one DID Exchange connection (a single handshake, `goal_code: "establish-connection"`). Over that one identity pair, their controllers then confirm **three independently-lifecycled DTL relationships** — `A delegates_to B`, `A depends_on B`, and `B can_send_message_to A` — each separately revocable (B may revoke `delegates_to` while `depends_on` still stands). The connection's `goal_code` types *one handshake's purpose*; it cannot represent N independently-confirmed, independently-revocable typed standing facts over the same identity pair. That gap — between typing the handshake and typing the standing relationship — is the daylight DTL occupies.
- **Verifiable agent delegation** (recent, 2026) — the **Agent Identity Protocol** (AIP; arXiv:2603.24775, with IETF draft `draft-prakash-aip-00`) defines *Invocation-Bound Capability Tokens* that fuse identity, attenuated authorization, and provenance for agent-to-agent delegation across MCP and A2A; **LDP** (arXiv:2603.08852, *"LDP: An Identity-Aware Protocol for Multi-Agent LLM Systems"*) similarly scopes delegated authority for multi-agent routing. These are the nearest *current* neighbors to the `delegates_to` type, but authorization flows **one way** (an issuer grants to a delegatee; the second party does not confirm a standing relationship), there is **no DTL standing-relationship lifecycle**, and there is **no open relationship-type vocabulary**. DTL differs on all three.
- **One-way attestation / reputation** — **W3C Verifiable Credentials** are the general standard here (an issuer makes signed claims about a subject); the draft ERC-8240 (*Trust Infrastructure for Agents and Assets* — a one-way trust layer in which evaluators submit signed, contestable attestations about agents and assets) is the agent-ecosystem instance. In both, one party asserts about another; there is no confirmation by the second party and no standing, directed, typed edge. Reciprocal issuance ("A issues a credential about B; B issues one about A") yields two independent one-way artifacts, not one confirmed record — no shared status, no propose/decline/withdraw semantics, and credential revocation is issuer-side status on one artifact, not a lifecycle both parties share. DTL differs in requiring two-party confirmation of a single record.
- **Generic labeled-edge models** — RDF and RDF-star triples, FOAF (`foaf:knows`), schema.org relations, and HTML **XFN** `rel` values express a typed, directed edge between two identified subjects, and are the broad precedent for an *open vocabulary of labeled relations*. But such a statement does not standardize DTL's **bilateral authorization and lifecycle**: it is published by one party, the *second* subject does not confirm it, and there is no lifecycle. DTL adds two-party confirmation and a lifecycle to the labeled edge.
- **The propose/accept and commitment lineage** — the **FIPA Contract Net Interaction Protocol** (FIPA SC00029H) is an early standardized *propose → accept/reject* handshake, but it types the *task* being bid and its lifecycle is per-interaction rather than a standing relationship. The **commitment-machine** line in multi-agent systems (Singh; Yolum & Singh, "Commitment Machines," ATAL 2001) is the closer ancestor of a *lifecycle-bearing* social relationship — a social commitment that is created and then discharged, cancelled, or released — though commitment machines model the *obligation's* semantics, whereas DTL types are deliberately non-behavioral (§4). DTL's `proposed → established → revoked/withdrawn` lifecycle is a small, two-party specialization in the spirit of that line. This *social-commitment* sense is distinct from the game-theoretic *commitment device* of the cooperative-AI literature (§1).
- **Social and presence graphs** — **ActivityPub** (with ActivityStreams `Follow` / `Accept` / `Reject` / `Undo`) and **XMPP** presence subscriptions (RFC 6121), as well as proprietary social friend-graphs, do implement a *confirmed, directed, lifecycle-bearing* relationship — but each ships a **single fixed relationship kind** (a follow, a presence subscription, a friendship), not an **open typed vocabulary** of standing relationships. ActivityStreams also defines an open-kinded `Relationship` object, but as a one-way *description*: the standard defines no confirmation flow and no lifecycle for it — only the fixed-kind follow is confirmed, so the open kind and the confirmed lifecycle never meet in a single construct. They occupy the confirmed/directed/lifecycle cell for *one* hard-coded type; DTL generalizes it to an open type vocabulary over arbitrary agent pairs.
- **WS-Agreement** (Open Grid Forum) — a two-party offer/accept agreement format with state, but a heavyweight SLA document for service-level guarantees rather than a minimal typed standing relationship between agent identities; it does not fill the cell.
- **Open agent-relationship and identity efforts (2025–2026)** — the **W3C AI Agent Protocol Community Group** (proposed 2025) names, among its goals, letting agents "dynamically establish or dissolve collaborations," but has not shipped a relationship primitive. Broader identity, discovery, and interoperability efforts — Microsoft **Entra Agent ID** (GA 2026), **AGNTCY**, **ANP**, **ACP**, **NANDA**, and **NIST**'s agent-identity work — address agent *identity*, *discovery*, or *messaging*, not a confirmed standing relationship between two specific agents.
- **Agent interaction protocols** (A2A, MCP) define *how* agents communicate, not a standing, confirmed relationship between two specific agents. DTL is complementary — a relationship record such protocols could reference.

---

## Appendix A. JSON Schema (Normative)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://opendtl.org/v0/relationship.schema.json",
  "title": "DTL Relationship Record",
  "$comment": "The constraint source != target is normative (see §3) but cannot be expressed in JSON Schema; implementations MUST enforce it externally.",
  "type": "object",
  "required": ["source", "target", "type", "status", "profile", "proofs"],
  "properties": {
    "id": {
      "type": "string",
      "description": "Optional unique identifier for the relationship record."
    },
    "source": {
      "type": "string",
      "minLength": 1,
      "description": "Identifier of the source agent (substrate-defined)."
    },
    "target": {
      "type": "string",
      "minLength": 1,
      "description": "Identifier of the target agent (substrate-defined). Must differ from source."
    },
    "type": {
      "type": "string",
      "minLength": 1,
      "description": "Exactly one relationship type, from an open vocabulary."
    },
    "status": {
      "type": "string",
      "enum": ["proposed", "established", "declined", "withdrawn", "revoked"]
    },
    "profile": {
      "type": "string",
      "description": "Confirmation profile that produced the proofs, e.g. 'attested' or 'signed'."
    },
    "proofs": {
      "type": "object",
      "description": "Proofs of authorization keyed by action; form defined by the confirmation profile.",
      "properties": {
        "proposal": { "type": "object" },
        "confirmation": { "type": "object" },
        "decline": { "type": "object" },
        "withdrawal": { "type": "object" },
        "revocation": { "type": "object" }
      },
      "additionalProperties": false
    },
    "description": { "type": "string" },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "$comment": "format: date-time is annotation-only in JSON Schema 2020-12 (here and in updated_at); a deployment MAY choose to assert it."
    },
    "updated_at": { "type": "string", "format": "date-time" },
    "ext": {
      "type": "object",
      "description": "Optional deployment- or substrate-specific extension fields (§3); contents are unconstrained."
    }
  },
  "additionalProperties": false,
  "allOf": [
    {
      "if": {
        "required": ["status"],
        "properties": { "status": { "const": "proposed" } }
      },
      "then": {
        "required": ["proofs"],
        "properties": {
          "proofs": {
            "required": ["proposal"],
            "not": { "anyOf": [
              { "required": ["confirmation"] },
              { "required": ["decline"] },
              { "required": ["withdrawal"] },
              { "required": ["revocation"] }
            ] }
          }
        }
      }
    },
    {
      "if": {
        "required": ["status"],
        "properties": { "status": { "const": "established" } }
      },
      "then": {
        "required": ["proofs"],
        "properties": {
          "proofs": {
            "required": ["proposal", "confirmation"],
            "not": { "anyOf": [
              { "required": ["decline"] },
              { "required": ["withdrawal"] },
              { "required": ["revocation"] }
            ] }
          }
        }
      }
    },
    {
      "if": {
        "required": ["status"],
        "properties": { "status": { "const": "declined" } }
      },
      "then": {
        "required": ["proofs"],
        "properties": {
          "proofs": {
            "required": ["proposal", "decline"],
            "not": { "anyOf": [
              { "required": ["confirmation"] },
              { "required": ["withdrawal"] },
              { "required": ["revocation"] }
            ] }
          }
        }
      }
    },
    {
      "if": {
        "required": ["status"],
        "properties": { "status": { "const": "withdrawn" } }
      },
      "then": {
        "required": ["proofs"],
        "properties": {
          "proofs": {
            "required": ["proposal", "withdrawal"],
            "not": { "anyOf": [
              { "required": ["confirmation"] },
              { "required": ["decline"] },
              { "required": ["revocation"] }
            ] }
          }
        }
      }
    },
    {
      "if": {
        "required": ["status"],
        "properties": { "status": { "const": "revoked" } }
      },
      "then": {
        "required": ["proofs"],
        "properties": {
          "proofs": {
            "required": ["proposal", "confirmation", "revocation"],
            "not": { "anyOf": [
              { "required": ["decline"] },
              { "required": ["withdrawal"] }
            ] }
          }
        }
      }
    }
  ]
}
```

---

## Appendix B. Examples (Informative)

**B.1 — `delegates_to`, ERC-8004 substrate, `attested` profile.**

```json
{
  "id": "rel:8004:42",
  "source": "11155111:123",
  "target": "11155111:456",
  "type": "delegates_to",
  "status": "established",
  "profile": "attested",
  "proofs": {
    "proposal": {
      "controller": "0xA11ce…",
      "attested_by": "attesting-service.example",
      "method": "siwe",
      "at": "2026-06-18T10:00:00Z"
    },
    "confirmation": {
      "controller": "0xB0b…",
      "attested_by": "attesting-service.example",
      "method": "siwe",
      "at": "2026-06-18T10:05:00Z"
    }
  },
  "created_at": "2026-06-18T10:00:00Z",
  "updated_at": "2026-06-18T10:05:00Z"
}
```

**B.2 — `depends_on`, non-blockchain substrate (did:web), `signed` profile.**

Demonstrates substrate-neutrality and the trustless profile: each controller signs the record directly, verifiable against its DID — and here each agent is its own controller (no human in the loop).

```json
{
  "id": "rel:example:2",
  "source": "did:web:alpha.example",
  "target": "did:web:beta.example",
  "type": "depends_on",
  "status": "established",
  "profile": "signed",
  "proofs": {
    "proposal": {
      "controller": "did:web:alpha.example",
      "verificationMethod": "did:web:alpha.example#key-1",
      "signature": "z3Jx…"
    },
    "confirmation": {
      "controller": "did:web:beta.example",
      "verificationMethod": "did:web:beta.example#key-1",
      "signature": "z58P…"
    }
  }
}
```

**B.3 — `delegates_to`, ERC-8004 substrate, `attested` profile, after revocation.**

A relationship that was established and then revoked; the `revocation` proof attributes the action to the revoking controller (here the target).

```json
{
  "id": "rel:8004:42",
  "source": "11155111:123",
  "target": "11155111:456",
  "type": "delegates_to",
  "status": "revoked",
  "profile": "attested",
  "proofs": {
    "proposal": {
      "controller": "0xA11ce…",
      "attested_by": "attesting-service.example",
      "method": "siwe",
      "at": "2026-06-18T10:00:00Z"
    },
    "confirmation": {
      "controller": "0xB0b…",
      "attested_by": "attesting-service.example",
      "method": "siwe",
      "at": "2026-06-18T10:05:00Z"
    },
    "revocation": {
      "controller": "0xB0b…",
      "attested_by": "attesting-service.example",
      "method": "siwe",
      "at": "2026-06-19T09:00:00Z"
    }
  },
  "created_at": "2026-06-18T10:00:00Z",
  "updated_at": "2026-06-19T09:00:00Z"
}
```

---

*End of v0.5 draft.*
