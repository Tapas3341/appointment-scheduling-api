# Design Decisions

## Provider profile and service schema

**Date:** 25 October 2026

**Decision:** Follow the canonical project plan: `provider_profiles.user_id` is
both the primary key and a foreign key to `users.id`. The profile contains a
required `display_name` and IANA timezone name. Services use a UUID `id` and
`provider_id` foreign key to `provider_profiles.user_id`, with a required
`name`, positive `duration_minutes`, and `is_active`.

**Implementation choices where the plan leaves details open:**

- `display_name` and service `name` use `VARCHAR(255)` and are non-null.
- `timezone` uses `VARCHAR(255)` and is non-null; API validation must check that
  values are valid IANA timezone identifiers.
- `duration_minutes` is an integer with a database `CHECK (duration_minutes > 0)`.
- `is_active` is non-null and defaults to `TRUE` in the database.
- `services.provider_id` is indexed for provider service lookups.
- Deleting a user cascades to the profile; deleting a profile cascades to its
  services because these records have no independent owner.
- Existing timezone-aware `created_at` and `updated_at` columns are retained on
  both tables.
- Existing profile display names are migrated from the owning user's
  `full_name`. The correction drops the unplanned `services.description`
  column; downgrade restores the nullable column but cannot recover values that
  were discarded during upgrade.

**Trade-offs:** A shared profile/user primary key makes ownership direct and
avoids a redundant profile identifier. The duration check preserves the
positive-duration invariant at the database boundary as well as the API.
