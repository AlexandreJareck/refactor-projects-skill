class HttpError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

function errorHandler(logger = console) {
    return (error, req, res, next) => {
        if (res.headersSent) return next(error);
        if (error instanceof HttpError) return res.status(error.status).send(error.message);
        logger.error('Unexpected request failure', { method: req.method, path: req.path, error: error.message });
        return res.status(500).send('Erro interno');
    };
}

module.exports = { HttpError, errorHandler };
