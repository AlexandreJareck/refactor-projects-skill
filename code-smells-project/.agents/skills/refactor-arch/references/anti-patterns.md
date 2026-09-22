# Anti-pattern catalog and severity

Classify demonstrated impact, not just a syntactic match. CRITICAL means a severe security or architecture failure; HIGH means strong MVC/SOLID violation or serious maintainability risk; MEDIUM means a moderate correctness, performance or consistency problem; LOW means local readability or naming debt. Cite the precise evidence and consider whether an apparent issue is already mitigated elsewhere.

| Pattern | Default severity | Detection signals | Remedy |
|---|---|---|---|
| Arbitrary query execution or SQL injection | CRITICAL | HTTP data reaches a raw SQL execution call, or untrusted values are concatenated into SQL strings | Remove arbitrary query endpoints; parameterize values and constrain operations |
| Exposed credentials or payment data | CRITICAL | Secrets, password hashes or full card numbers appear in responses, logs or source | Remove exposure; use environment configuration and safe serializers/logging |
| Weak password storage | CRITICAL | Plaintext, MD5, SHA alone, Base64 or a custom fast hash is used for passwords | Use a password-specific hashing library and adapt login/seed paths |
| God class with complete responsibility collapse | CRITICAL | One class/function owns routing, database access, complex domain workflows and HTTP presentation for multiple domains | Separate route, controller and model responsibilities by domain |
| Cross-layer business logic | HIGH | Routes contain substantial checkout, report or state-transition logic; models format HTTP responses | Move orchestration to controllers; keep routes thin and models data-focused |
| Global mutable state | HIGH | Connection, cache or counters are shared mutable globals across requests without lifecycle controls | Scope state and inject dependencies; use appropriate storage |
| Partial multi-step write | MEDIUM | A workflow writes several related records without a transaction or ignores a callback error | Use a transaction and handle every write failure |
| N+1 queries | MEDIUM | A database query is issued inside a loop over result rows | Join, prefetch or aggregate in bounded queries |
| Repeated or missing validation | MEDIUM | Similar routes duplicate rules inconsistently, or an input reaches business logic without required checks | Centralize validation with explicit error mapping |
| Deprecated API | MEDIUM | A call is documented as deprecated for the installed library version; verify official docs or release notes | Name the verified modern equivalent and migration effect |
| Magic values | LOW | Repeated statuses, limits or domain options are embedded as literals | Name a shared domain constant where it improves clarity |
| Poor names or unused imports | LOW | Ambiguous local variables or unused imports obscure a workflow | Rename locals and remove unused imports |

Review all categories even if none is found. A catalog entry is a search hypothesis, not a report finding. Security findings may warrant a higher severity when the concrete exploit path is demonstrated. Never claim an API is deprecated solely because it looks old.
