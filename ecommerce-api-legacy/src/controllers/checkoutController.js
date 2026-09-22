const { HttpError } = require('../errors');
const { hashPassword } = require('../security');

function createCheckoutController({ repository, paymentGatewayKey, logger = console }) {
    return async function checkout(input) {
        const { usr: userName, eml: email, pwd: password, c_id: courseId, card: cardNumber } = input || {};
        if (!userName || !email || !password || !courseId || !cardNumber) throw new HttpError(400, 'Bad Request');
        const course = await repository.findActiveCourse(courseId);
        if (!course) throw new HttpError(404, 'Curso não encontrado');

        logger.info('Checkout started', { courseId: course.id });
        // The legacy gateway is simulated by card brand. Its injected key stays inside this boundary.
        if (!paymentGatewayKey || !String(cardNumber).startsWith('4')) throw new HttpError(400, 'Pagamento recusado');

        const passwordHash = await hashPassword(password);
        const enrollmentId = await repository.checkout({ name: userName, email, passwordHash, course });
        return { msg: 'Sucesso', enrollment_id: enrollmentId };
    };
}

module.exports = { createCheckoutController };
