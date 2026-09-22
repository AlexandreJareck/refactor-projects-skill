# Refactoring playbook

Adapt each transformation to the installed framework and existing architecture. The snippets illustrate a local before/after change; they are not complete application scaffolds.

Catalog mapping: arbitrary SQL → 1–2; exposed secrets or payment data → 3, 11, 13; weak passwords → 4; God class and cross-layer logic → 5; global mutable state → 14; partial writes → 6; N+1 → 7; repeated validation → 9; deprecated API → 10; magic values, poor names and unused imports → 12.

## 1. Parameterize SQL

Before: `cursor.execute("SELECT * FROM users WHERE email='" + email + "'")`

After: `cursor.execute("SELECT * FROM users WHERE email = ?", (email,))`

## 2. Remove arbitrary query routes

Before: `app.post('/admin/query', (req, res) => db.run(req.body.sql))`

After: `router.get('/admin/report', requireAdmin, reportController.summary)` where `summary` performs a fixed, parameterized read. If authentication is unavailable, remove or disable the dangerous route and document the changed contract.

## 3. Move configuration to environment

Before: `const gatewayKey = 'pk_live_example'`

After: `const gatewayKey = process.env.PAYMENT_GATEWAY_KEY` plus startup validation if required. Put only variable names in `.env.example`.

## 4. Replace weak password storage

Before: `hashlib.md5(password.encode()).hexdigest()`

After: `generate_password_hash(password)` and `check_password_hash(stored, password)` using Werkzeug or another maintained password library. Update seed and login together; plan migration for existing user rows.

## 5. Extract a controller from a route

Before: `@bp.post('/tasks')` contains validation, SQL writes and `jsonify(...)`.

After: `@bp.post('/tasks')` parses input and calls `task_controller.create(data)`; the controller coordinates validation and model writes; the route serializes the result.

## 6. Enclose multi-step writes in a transaction

Before: `insertEnrollment(); insertPayment(); insertAudit(); sendSuccess()` with independent commits.

After: begin transaction, write all required records, commit on success, roll back on any failure, then respond. Await or check each callback/promise before committing.

## 7. Replace N+1 loops

Before: `for user in users: tasks = Task.query.filter_by(user_id=user.id).all()`

After: aggregate task counts by `user_id` once or load related tasks with a supported eager-loading strategy, then assemble results.

## 8. Centralize error handling

Before: every route uses `except Exception as e: return jsonify({'error': str(e)}), 500`.

After: routes raise typed expected errors; one Flask error handler or Express error middleware maps them to stable responses and logs unexpected exceptions without exposing internals.

## 9. Centralize validation

Before: create and update routes each embed similar product limits with missing cases.

After: both call `validate_product(data)` or a shared schema and return the same field-specific errors.

## 10. Replace a verified deprecated call

Before: `User.query.get(user_id)` *only when documentation for the installed SQLAlchemy version confirms it is legacy/deprecated*.

After: `db.session.get(User, user_id)`; check the surrounding session lifecycle and test not-found behavior.

## 11. Safe response projection

Before: `return jsonify(user.__dict__)` or a `to_dict` method that includes `password`.

After: project explicit public fields (`id`, `name`, `email`, etc.) and assert that credentials never appear in responses.

## 12. Clear names and constants

Before: `let e = req.body.eml; if (status === 'PAID') ...`

After: `const email = req.body.eml; if (status === PaymentStatus.PAID) ...`, retaining the external request key if required for compatibility.

## 13. Redact sensitive logs

Before: ``console.log(`Charging ${cardNumber} with ${gatewayKey}`)``.

After: `logger.info('Checkout started', { requestId, courseId })`; keep card details and keys out of logs and errors. Test that logs contain neither value.

## 14. Remove mutable cross-request globals

Before: `let totalRevenue = 0; function checkout() { totalRevenue += amount }` in a shared module.

After: `async function revenue(repository) { return repository.sumPaidPayments() }`; pass a repository into the controller and derive the value from persistent data. For database connections, create a scoped connection and close it at the end of the request.
