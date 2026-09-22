const { HttpError } = require('../errors');

function createAdminController({ repository }) {
    return {
        async financialReport() {
            const rows = await repository.financialReport();
            const report = new Map();
            for (const row of rows) {
                if (!report.has(row.id)) report.set(row.id, { course: row.course, revenue: 0, students: [] });
                if (row.enrollment_id === null) continue;
                const course = report.get(row.id);
                if (row.status === 'PAID') course.revenue += row.amount;
                course.students.push({ student: row.student, paid: row.amount || 0 });
            }
            return [...report.values()];
        },

        async deleteUser(userId) {
            const changes = await repository.deleteUser(userId);
            if (!changes) throw new HttpError(404, 'Usuário não encontrado');
            return 'Usuário deletado';
        },
    };
}

module.exports = { createAdminController };
