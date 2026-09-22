const sqlite3 = require('sqlite3');

class LmsRepository {
    constructor({ filename = ':memory:', db } = {}) {
        this.db = db || new sqlite3.Database(filename);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.db.run(sql, params, function onRun(error) {
                if (error) reject(error);
                else resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => this.db.get(sql, params, (error, row) => error ? reject(error) : resolve(row)));
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => this.db.all(sql, params, (error, rows) => error ? reject(error) : resolve(rows)));
    }

    async initialize({ seed = true, seedPasswordHash } = {}) {
        await this.run('PRAGMA foreign_keys = ON');
        await this.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, pass TEXT NOT NULL)');
        await this.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT NOT NULL, price REAL NOT NULL, active INTEGER NOT NULL)');
        await this.run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, course_id INTEGER NOT NULL REFERENCES courses(id))');
        await this.run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE, amount REAL NOT NULL, status TEXT NOT NULL)');
        await this.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT NOT NULL, created_at DATETIME NOT NULL)');
        if (!seed) return;
        await this.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', ['Leonan', 'leonan@fullcycle.com.br', seedPasswordHash]);
        await this.run("INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)");
        await this.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await this.run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
    }

    findActiveCourse(courseId) {
        return this.get('SELECT id, title, price FROM courses WHERE id = ? AND active = 1', [courseId]);
    }

    findUserByEmail(email) {
        return this.get('SELECT id FROM users WHERE email = ?', [email]);
    }

    async checkout({ name, email, passwordHash, course }) {
        await this.run('BEGIN IMMEDIATE');
        try {
            let user = await this.findUserByEmail(email);
            if (!user) {
                const inserted = await this.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
                user = { id: inserted.lastID };
            }
            const enrollment = await this.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [user.id, course.id]);
            await this.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [enrollment.lastID, course.price, 'PAID']);
            await this.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [`Checkout curso ${course.id} por ${user.id}`]);
            await this.run('COMMIT');
            return enrollment.lastID;
        } catch (error) {
            try { await this.run('ROLLBACK'); } catch (_) { /* keep the original error */ }
            throw error;
        }
    }

    financialReport() {
        return this.all(`SELECT c.id, c.title AS course, e.id AS enrollment_id,
                                u.name AS student, p.amount, p.status
                           FROM courses c
                      LEFT JOIN enrollments e ON e.course_id = c.id
                      LEFT JOIN users u ON u.id = e.user_id
                      LEFT JOIN payments p ON p.enrollment_id = e.id
                       ORDER BY c.id, e.id`);
    }

    async deleteUser(userId) {
        await this.run('BEGIN IMMEDIATE');
        try {
            const result = await this.run('DELETE FROM users WHERE id = ?', [userId]);
            await this.run('COMMIT');
            return result.changes;
        } catch (error) {
            try { await this.run('ROLLBACK'); } catch (_) { /* keep the original error */ }
            throw error;
        }
    }

    close() {
        return new Promise((resolve, reject) => this.db.close(error => error ? reject(error) : resolve()));
    }
}

module.exports = LmsRepository;
