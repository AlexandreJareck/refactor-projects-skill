const test = require('node:test');
const assert = require('node:assert/strict');
const { createApplication } = require('../src/app');
const { loadConfig } = require('../src/config');

const config = { port: 0, adminApiKey: 'test-admin-key', paymentGatewayKey: 'test-gateway-key' };

test('configuration requires externally supplied secrets', () => {
    assert.throws(() => loadConfig({}), /ADMIN_API_KEY is required/);
    assert.throws(() => loadConfig({ ADMIN_API_KEY: 'admin' }), /PAYMENT_GATEWAY_KEY is required/);
    assert.deepEqual(loadConfig({ PORT: '4321', ADMIN_API_KEY: 'admin', PAYMENT_GATEWAY_KEY: 'gateway' }), {
        port: 4321, adminApiKey: 'admin', paymentGatewayKey: 'gateway',
    });
});

async function fixture() {
    const logEntries = [];
    const logger = {
        info(message, details) { logEntries.push({ level: 'info', message, details }); },
        error(message, details) { logEntries.push({ level: 'error', message, details }); },
    };
    const instance = await createApplication({ config, logger, seedPassword: 'seed-test-password' });
    const server = await new Promise(resolve => {
        const listening = instance.app.listen(0, '127.0.0.1', () => resolve(listening));
    });
    const baseUrl = `http://127.0.0.1:${server.address().port}`;
    return {
        ...instance,
        logEntries,
        async request(path, { method = 'GET', body, admin = false } = {}) {
            const headers = {};
            if (body !== undefined) headers['Content-Type'] = 'application/json';
            if (admin) headers['X-Admin-Key'] = config.adminApiKey;
            const response = await fetch(baseUrl + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
            const text = await response.text();
            let data;
            try { data = JSON.parse(text); } catch (_) { data = text; }
            return { status: response.status, data };
        },
        async close() {
            await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
            await instance.repository.close();
        },
    };
}

test('application initializes with isolated seeded data and scrypt password', async t => {
    const app = await fixture();
    t.after(() => app.close());
    const counts = await app.repository.get(`SELECT
        (SELECT COUNT(*) FROM users) AS users,
        (SELECT COUNT(*) FROM enrollments) AS enrollments,
        (SELECT COUNT(*) FROM payments) AS payments`);
    assert.deepEqual(counts, { users: 1, enrollments: 1, payments: 1 });
    const seed = await app.repository.get('SELECT pass FROM users WHERE id = 1');
    assert.match(seed.pass, /^scrypt:[0-9a-f]{32}:[0-9a-f]{128}$/);
});

test('all api.http flows preserve compatible responses and protect admin routes', async t => {
    const app = await fixture();
    t.after(() => app.close());
    const approvedCard = '4111222233334444';

    const approved = await app.request('/api/checkout', { method: 'POST', body: {
        usr: 'Guilherme', eml: 'gui@fullcycle.com.br', pwd: 'senhaforte', c_id: 2, card: approvedCard,
    } });
    assert.deepEqual(approved, { status: 200, data: { msg: 'Sucesso', enrollment_id: 2 } });

    const denied = await app.request('/api/checkout', { method: 'POST', body: {
        usr: 'João', eml: 'joao@teste.com', pwd: '123', c_id: 1, card: '5111222233334444',
    } });
    assert.deepEqual(denied, { status: 400, data: 'Pagamento recusado' });
    assert.equal((await app.repository.get("SELECT COUNT(*) AS count FROM users WHERE email = 'joao@teste.com'")).count, 0);

    assert.deepEqual(await app.request('/api/admin/financial-report'), { status: 403, data: 'Acesso negado' });
    const report = await app.request('/api/admin/financial-report', { admin: true });
    assert.equal(report.status, 200);
    assert.deepEqual(report.data, [
        { course: 'Clean Architecture', revenue: 997, students: [{ student: 'Leonan', paid: 997 }] },
        { course: 'Docker', revenue: 497, students: [{ student: 'Guilherme', paid: 497 }] },
    ]);

    assert.deepEqual(await app.request('/api/users/1', { method: 'DELETE' }), { status: 403, data: 'Acesso negado' });
    assert.deepEqual(await app.request('/api/users/1', { method: 'DELETE', admin: true }), { status: 200, data: 'Usuário deletado' });
    assert.deepEqual(await app.repository.get('SELECT COUNT(*) AS enrollments FROM enrollments WHERE user_id = 1'), { enrollments: 0 });
    assert.deepEqual(await app.repository.get('SELECT COUNT(*) AS payments FROM payments WHERE enrollment_id = 1'), { payments: 0 });

    const serializedLogs = JSON.stringify(app.logEntries);
    assert.equal(serializedLogs.includes(approvedCard), false);
    assert.equal(serializedLogs.includes(config.paymentGatewayKey), false);
});

test('every original endpoint has representative validation or not-found behavior', async t => {
    const app = await fixture();
    t.after(() => app.close());

    assert.deepEqual(await app.request('/api/checkout', { method: 'POST', body: { usr: 'X' } }), { status: 400, data: 'Bad Request' });
    assert.deepEqual(await app.request('/api/checkout', { method: 'POST', body: {
        usr: 'X', eml: 'x@example.test', pwd: 'password', c_id: 999, card: '4111222233334444',
    } }), { status: 404, data: 'Curso não encontrado' });
    assert.deepEqual(await app.request('/api/admin/financial-report'), { status: 403, data: 'Acesso negado' });
    assert.deepEqual(await app.request('/api/users/999', { method: 'DELETE', admin: true }), { status: 404, data: 'Usuário não encontrado' });
});

test('checkout rolls back user and enrollment when payment write fails', async t => {
    const app = await fixture();
    t.after(() => app.close());
    await app.repository.run(`CREATE TRIGGER fail_new_payment BEFORE INSERT ON payments
        WHEN NEW.enrollment_id > 1 BEGIN SELECT RAISE(ABORT, 'isolated fault'); END`);

    const response = await app.request('/api/checkout', { method: 'POST', body: {
        usr: 'Fault', eml: 'fault@example.test', pwd: 'password', c_id: 2, card: '4111222233334444',
    } });
    assert.deepEqual(response, { status: 500, data: 'Erro interno' });
    assert.equal((await app.repository.get("SELECT COUNT(*) AS count FROM users WHERE email = 'fault@example.test'")).count, 0);
    assert.equal((await app.repository.get('SELECT COUNT(*) AS count FROM enrollments WHERE id > 1')).count, 0);
    assert.equal((await app.repository.get('SELECT COUNT(*) AS count FROM payments WHERE id > 1')).count, 0);
    assert.equal(app.logEntries.some(entry => entry.level === 'error' && entry.details.error.includes('isolated fault')), true);
});
