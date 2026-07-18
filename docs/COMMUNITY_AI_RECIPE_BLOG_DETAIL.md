# Community AI Recipe Blog Detail

## Status

Proposed for the v0.8 Social and Sharing milestone.

## Design source

- [Figma Make — Recipe app](https://www.figma.com/make/ZWjcbwIiSfT0io7tPwH38z/Recipe-app?t=bhWCTjL38rqAf4Ze-0)

The Figma concept is the visual reference for the community blog detail experience. This document is the product and engineering source of truth when implementation details are not explicit in the design.

## Summary

Add a public community area where authenticated users can publish AI-generated recipes as story-led blog posts. This document defines the detail page for one community post.

The page should help readers answer:

1. What is the story behind this recipe?
2. Can I trust where the recipe and nutrition information came from?
3. Can I cook it successfully?
4. Does it fit my preferences?
5. Can I save, share, or discuss it safely?

## Goals

- Turn a generated recipe into a readable, shareable community story.
- Preserve structured recipe data for cooking, saving, shopping, and accessibility.
- Clearly disclose AI generation, edits, nutrition uncertainty, and safety review.
- Give authors identity and ownership without exposing private profile data.
- Support constructive engagement through reactions, comments, saves, shares, and reports.
- Make the page excellent on mobile and installable PWA surfaces.

## Non-goals

- Medical advice, diagnosis, or treatment recommendations.
- An unrestricted publishing system without authentication and moderation.
- Real-time collaborative editing.
- Creator monetization in the first release.
- Public exposure of private recipes, profiles, food history, or health preferences.
- Treating AI-generated nutrition estimates as verified clinical data.

## User stories

- As a visitor, I can read a community recipe without creating an account.
- As a signed-in user, I can save, react to, comment on, share, and report a post.
- As an author, I can publish a saved AI recipe with my own story and edits.
- As an author, I can preview and unpublish my post.
- As a reader, I can see AI provenance, author edits, nutrition confidence, allergens, and safety notes.
- As a moderator, I can review reported posts and comments and record an auditable decision.

## Information architecture

### Route

`/community/recipes/{slug}`

Use a stable public ID internally. Slugs are human-readable and may change without changing identity.

### Page order

1. Global header and community navigation
2. Breadcrumb or back-to-community link
3. Hero image
4. Title, summary, cuisine, tags, and author block
5. AI provenance and safety disclosure
6. Primary actions: Save, Share, Start cooking
7. Recipe facts: servings, prep time, cook time, difficulty
8. Author story
9. Ingredients with serving adjustment
10. Step-by-step instructions
11. Nutrition estimate and uncertainty note
12. Substitutions, allergens, dietary labels, and safety warnings
13. Optional shopping actions
14. Reactions and comments
15. Related community recipes
16. Report content and legal links

On narrow screens, primary actions should remain reachable without hiding safety information.

## UX requirements

### Hero and identity

- Use a meaningful food image with descriptive alt text.
- Show the post title, a short deck, author display name/avatar, and publication date.
- Show edited and updated states when applicable.
- Do not expose an email address or private account attributes.

### AI transparency

Display a persistent disclosure near the title:

> AI-generated recipe, reviewed and edited by the author.

Also show:

- AI provider or `local-fallback`
- generation date
- whether ingredients or steps were edited after generation
- safety review state
- nutrition source and confidence
- link to “How GlucoPlate uses AI”

Do not label content as verified unless a defined verification process completed successfully.

### Recipe content

- Keep ingredients structured as quantity, unit, item, preparation, and optional note.
- Allow serving adjustment while retaining the original published quantities.
- Number steps and support timers or cooking-mode links later.
- Make substitutions and allergen warnings visible before cooking begins.
- Label nutrition as an estimate and preserve the existing wellness disclaimer.
- Reuse saved-recipe and cart workflows rather than duplicating recipe data.

### Engagement

Anonymous visitors may read and share. Authentication is required to:

- save
- react
- comment
- publish
- report

Comments should support plain text only in the first release. Sanitize all user-authored content and links. Show optimistic UI only when failure can be reversed cleanly.

### States

The design must include:

- loading skeleton
- not found
- unpublished or removed
- offline cached view
- image unavailable
- comments empty
- comments unavailable
- action requires sign-in
- report submitted
- safety warning
- content under review

## Accessibility

- Meet WCAG 2.2 AA for contrast, focus visibility, semantics, and keyboard navigation.
- Use one `h1` and a logical heading hierarchy.
- Provide skip links and landmarks.
- Announce save, share, reaction, and report outcomes through an ARIA live region.
- Do not encode dietary or safety status through color alone.
- Keep tap targets at least 44 by 44 CSS pixels.
- Respect reduced motion and text resizing.
- Preserve readable ingredient and step layouts at 200% zoom.

## Content and data model

### CommunityPost

- `id`
- `slug`
- `author_id`
- `recipe_id`
- `title`
- `summary`
- `story_markdown`
- `hero_image_url`
- `hero_image_alt`
- `status`: draft, published, under_review, removed, archived
- `visibility`: public, unlisted
- `published_at`
- `updated_at`
- `moderation_state`
- `reaction_count`
- `comment_count`
- `save_count`

### PublishedRecipeSnapshot

A published post must reference an immutable snapshot so later private recipe edits do not silently alter public content.

- title and summary
- servings and time estimates
- cuisine and tags
- structured ingredients
- structured steps
- substitutions
- allergen and dietary labels
- nutrition estimate plus source/confidence
- safety review
- AI provider and generation timestamp
- author-edit metadata
- schema version

### CommunityComment

- `id`
- `post_id`
- `author_id`
- `body`
- `status`: visible, under_review, removed
- `created_at`
- `updated_at`

### CommunityReport

- `id`
- reporter, target type, and target ID
- reason code and optional details
- status and moderator decision
- timestamps and audit metadata

## Proposed API

### Public reads

- `GET /api/community/posts?cursor=&cuisine=&tag=&sort=`
- `GET /api/community/posts/{slug}`
- `GET /api/community/posts/{post_id}/comments?cursor=`

### Authenticated actions

- `POST /api/community/posts`
- `PATCH /api/community/posts/{post_id}`
- `POST /api/community/posts/{post_id}/publish`
- `POST /api/community/posts/{post_id}/unpublish`
- `POST /api/community/posts/{post_id}/reactions`
- `DELETE /api/community/posts/{post_id}/reactions/{reaction}`
- `POST /api/community/posts/{post_id}/comments`
- `PATCH /api/community/comments/{comment_id}`
- `DELETE /api/community/comments/{comment_id}`
- `POST /api/community/reports`

Mutation endpoints require authentication, authorization, CSRF protection where applicable, rate limits, and idempotency handling for repeated client actions.

## Publishing flow

1. User saves or generates a recipe.
2. User chooses “Share with community.”
3. System creates a draft with a recipe snapshot.
4. Author adds a story, hero image, alt text, and public tags.
5. System reruns schema validation and safety checks.
6. Author previews AI and nutrition disclosures.
7. Author confirms publication.
8. Post becomes public or enters moderation based on policy.
9. Search/feed indexing happens asynchronously.

## Trust, safety, and moderation

- Run the existing recipe safety review again at publish time.
- Block medical claims, medication advice, dangerous food handling, and disallowed content.
- Require allergen and nutrition uncertainty disclosures.
- Scan uploaded images and strip embedded metadata.
- Rate-limit publishing, comments, reactions, and reports.
- Allow users to report unsafe recipes, harassment, spam, impersonation, copyright concerns, and other issues.
- Preserve moderation audit records separately from public content.
- Define appeal and restoration workflows before production launch.
- Never allow prompt text or generated content to bypass output validation and sanitization.

## Privacy and ownership

- Publishing requires explicit confirmation; recipes remain private by default.
- Store the public snapshot separately from private generation history.
- Authors may unpublish content, subject to retention and moderation policy.
- Define licenses or sharing terms for community posts and images before launch.
- Avoid exposing prompts, dietary profiles, location, shopping history, or hidden safety metadata.
- Provide account-deletion and content-export behavior before v1.0.

## Performance and SEO

- Render public post metadata for link previews and search indexing.
- Include canonical URL, Open Graph data, and Recipe/Article structured data where accurate.
- Lazy-load below-the-fold media and related posts.
- Reserve image dimensions to avoid layout shifts.
- Target Core Web Vitals in the “good” range on representative mobile devices.
- Cache public reads while invalidating promptly after moderation or unpublishing.

## Analytics

Track privacy-conscious product events:

- post viewed
- recipe saved from community
- cooking mode started
- share initiated
- reaction added
- comment created
- report submitted
- author publish completed
- safety or moderation block

Do not include story text, comments, prompts, health preferences, or ingredient details in analytics payloads.

## Acceptance criteria

- A public visitor can open a published post by slug and read the complete recipe.
- The page visibly identifies AI provenance, author edits, nutrition uncertainty, and safety status.
- Signed-in users can save, share, react, comment, and report with accessible feedback.
- Only the author or an authorized moderator can edit or unpublish a post.
- Publication creates an immutable recipe snapshot.
- Private recipe and profile fields never appear in the public response.
- Removed and under-review content returns an intentional user-facing state.
- The page works at mobile, tablet, and desktop widths and meets WCAG 2.2 AA.
- API tests cover authorization, publication, snapshots, moderation states, pagination, sanitization, and rate limits.
- End-to-end tests cover read, publish, save, comment, report, unpublish, offline, and not-found flows.

## Delivery slices

### Slice 1 — Read-only detail

- schemas and repository
- seeded published posts
- public detail API
- responsive detail page
- provenance, nutrition, safety, and error states

### Slice 2 — Authenticated publishing

- Firebase Authentication ownership
- draft/preview/publish flow
- immutable snapshots
- save and share actions

### Slice 3 — Community engagement

- reactions
- comments
- reports
- moderation queue and audit trail

### Slice 4 — Discovery and hardening

- community feed and filters
- related posts
- SEO and structured data
- analytics, performance, accessibility, and abuse testing

## Open decisions

- Whether first publication is immediate or pre-moderated.
- Supported image source: generated gallery only, user upload, or both.
- Community content license and reuse terms.
- Comment threading depth and edit window.
- Reaction set.
- Whether unlisted posts are included in related content.
- Whether nutrition may be recalculated after publication without creating a new snapshot version.
