function loadConfig(env = process.env) {
    const port = Number(env.PORT || 3000);
    const adminApiKey = env.ADMIN_API_KEY;
    const paymentGatewayKey = env.PAYMENT_GATEWAY_KEY;

    if (!Number.isInteger(port) || port < 0 || port > 65535) throw new Error('PORT must be an integer between 0 and 65535');
    if (!adminApiKey) throw new Error('ADMIN_API_KEY is required');
    if (!paymentGatewayKey) throw new Error('PAYMENT_GATEWAY_KEY is required');
    return { port, adminApiKey, paymentGatewayKey };
}

module.exports = { loadConfig };
