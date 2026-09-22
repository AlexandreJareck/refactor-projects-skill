const express = require('express');
const { randomBytes } = require('node:crypto');
const { loadConfig } = require('./config');
const { errorHandler } = require('./errors');
const { hashPassword } = require('./security');
const LmsRepository = require('./models/LmsRepository');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createAdminController } = require('./controllers/adminController');
const { createApiRouter } = require('./routes/apiRoutes');

async function createApplication(options = {}) {
    const config = options.config || loadConfig();
    const logger = options.logger || console;
    const repository = options.repository || new LmsRepository({ filename: options.databaseFile });
    if (options.initialize !== false) {
        const seedPassword = options.seedPassword || randomBytes(32).toString('hex');
        const seedPasswordHash = await hashPassword(seedPassword);
        await repository.initialize({ seed: options.seed !== false, seedPasswordHash });
    }

    const app = express();
    app.use(express.json());
    const checkout = createCheckoutController({ repository, paymentGatewayKey: config.paymentGatewayKey, logger });
    const admin = createAdminController({ repository });
    app.use('/api', createApiRouter({ checkout, admin, adminApiKey: config.adminApiKey }));
    app.use(errorHandler(logger));
    return { app, repository, config };
}

async function start() {
    const { app, config } = await createApplication();
    return app.listen(config.port, () => console.log(`LMS rodando na porta ${config.port}`));
}

if (require.main === module) {
    start().catch(error => {
        console.error(`Falha ao iniciar: ${error.message}`);
        process.exitCode = 1;
    });
}

module.exports = { createApplication, start };
