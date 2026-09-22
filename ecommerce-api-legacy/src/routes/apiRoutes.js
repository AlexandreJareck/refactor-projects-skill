const express = require('express');
const { HttpError } = require('../errors');

function createApiRouter({ checkout, admin, adminApiKey }) {
    const router = express.Router();
    const asyncRoute = handler => (req, res, next) => Promise.resolve(handler(req, res)).catch(next);
    const requireAdmin = (req, res, next) => req.get('X-Admin-Key') === adminApiKey ? next() : next(new HttpError(403, 'Acesso negado'));

    router.post('/checkout', asyncRoute(async (req, res) => res.status(200).json(await checkout(req.body))));
    router.get('/admin/financial-report', requireAdmin, asyncRoute(async (req, res) => res.json(await admin.financialReport())));
    router.delete('/users/:id', requireAdmin, asyncRoute(async (req, res) => res.send(await admin.deleteUser(req.params.id))));
    return router;
}

module.exports = { createApiRouter };
