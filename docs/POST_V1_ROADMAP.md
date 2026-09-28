# SGTP Post-V1 Roadmap and Small Enhancement Lane

## Release gate

This is a deferred-work register, not implementation authorization. Post-V1 implementation may begin only after Phase 10 acceptance and the complete V1 Definition of Done in `docs/PRODUCT_DEFINITION.md` pass. Phase/task confirmation remains mandatory. Client feedback or Staging review alone is not authorization.

## V1.1 / early Post-V1 candidates

- Client tags (VIP, Regular, Urgent, Credit Customer)
- Barcode/QR Work tracking
- Rich Notification Center
- SMS/WhatsApp customer automation (requires provider/privacy approval)
- Rich searchable Audit Log UI
- Advanced password recovery
- Session/device management and revocation
- Login security history
- Advanced keyboard-first workflow
- PWA installation
- Expanded inventory/material stock
- Advanced production assignment and rework/correction workflows
- Feature flags, operational analytics and advanced monitoring dashboards

## Later / advanced candidates

- Offline-first operation, offline drafts, synchronization and conflict resolution
- AI Assistant, AI report summary, AI-assisted Client/Work search
- Smart Translation Assist, preserving original text
- Advanced analytics: completion-time, bottleneck, repeat-customer, revenue/outstanding trends and operational intelligence
- Advanced security analytics, rollout systems and observability

## Privacy and retention decisions required before Production

Policy must be decided before Phase 10 acceptance for active/deleted Clients, Related Persons, measurements, design/reference photos, financial records, invoices, receipts, audit/security/login records, notifications, backups, generated documents, anonymization and account deletion. Safe automation may be deferred; the policy itself may not. Retention durations remain `BUSINESS DECISION REQUIRED` until approved.

## Controlled Small Enhancement Lane

During an already confirmed task, a tiny directly related improvement may be included only if **all** conditions hold:

- Directly related to the active task and testable within it.
- Adds no business rule, architecture, role/authority, workflow state, tenant-boundary change, breaking API, major entity/module, destructive migration, Post-V1 feature, or security weakening.
- Reported explicitly in the task completion report.

Examples: accessibility correction, loading/error/empty-state refinement, harmless validation UX, search debounce, safe query optimization, request-ID/logging improvement, test improvement, or documentation/schema correction.

If uncertain, do not implement it; propose a separately scoped task and await its task confirmation.
