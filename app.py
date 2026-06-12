from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import calendar

app = Flask(__name__)
app.config['SECRET_KEY'] = 'expense-tracker-secret-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

CATEGORIES = [
    ('housing', 'السكن والإيجار', '🏠'),
    ('food', 'الطعام والمشتريات', '🍔'),
    ('transport', 'المواصلات', '🚗'),
    ('health', 'الصحة والطب', '💊'),
    ('education', 'التعليم', '📚'),
    ('entertainment', 'الترفيه', '🎬'),
    ('clothing', 'الملابس', '👔'),
    ('utilities', 'الفواتير والخدمات', '💡'),
    ('savings', 'الادخار', '💰'),
    ('other', 'أخرى', '📦'),
]

INCOME_SOURCES = [
    ('salary', 'الراتب الأساسي', '💼'),
    ('freelance', 'العمل الحر', '💻'),
    ('investment', 'الاستثمارات', '📈'),
    ('rental', 'الإيجارات', '🏘️'),
    ('other', 'أخرى', '💵'),
]


class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, default=date.today)
    month = db.Column(db.Integer)
    year = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.date:
            self.month = self.date.month
            self.year = self.date.year


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, default=date.today)
    month = db.Column(db.Integer)
    year = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.date:
            self.month = self.date.month
            self.year = self.date.year


with app.app_context():
    db.create_all()


def get_category_info(key):
    for cat in CATEGORIES:
        if cat[0] == key:
            return cat
    return (key, key, '📦')


def get_source_info(key):
    for src in INCOME_SOURCES:
        if src[0] == key:
            return src
    return (key, key, '💵')


@app.route('/')
def index():
    today = date.today()
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)

    incomes = Income.query.filter_by(month=month, year=year).all()
    expenses = Expense.query.filter_by(month=month, year=year).all()

    total_income = sum(i.amount for i in incomes)
    total_expense = sum(e.amount for e in expenses)
    balance = total_income - total_expense
    saving_rate = (balance / total_income * 100) if total_income > 0 else 0

    expense_by_category = {}
    for exp in expenses:
        expense_by_category[exp.category] = expense_by_category.get(exp.category, 0) + exp.amount

    months_list = [(m, calendar.month_name[m]) for m in range(1, 13)]
    years_list = list(range(today.year - 2, today.year + 2))

    arabic_months = {
        1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
        5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
        9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
    }

    return render_template('index.html',
        incomes=incomes,
        expenses=expenses,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        saving_rate=saving_rate,
        expense_by_category=expense_by_category,
        categories=CATEGORIES,
        income_sources=INCOME_SOURCES,
        current_month=month,
        current_year=year,
        years_list=years_list,
        arabic_months=arabic_months,
        get_category_info=get_category_info,
        get_source_info=get_source_info,
    )


@app.route('/add_income', methods=['POST'])
def add_income():
    amount = float(request.form['amount'])
    source = request.form['source']
    description = request.form.get('description', '')
    date_str = request.form['date']
    entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    income = Income(amount=amount, source=source, description=description, date=entry_date)
    db.session.add(income)
    db.session.commit()
    flash('تمت إضافة الدخل بنجاح ✅', 'success')
    return redirect(url_for('index', month=entry_date.month, year=entry_date.year))


@app.route('/add_expense', methods=['POST'])
def add_expense():
    amount = float(request.form['amount'])
    category = request.form['category']
    description = request.form.get('description', '')
    date_str = request.form['date']
    entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    expense = Expense(amount=amount, category=category, description=description, date=entry_date)
    db.session.add(expense)
    db.session.commit()
    flash('تمت إضافة المصروف بنجاح ✅', 'success')
    return redirect(url_for('index', month=entry_date.month, year=entry_date.year))


@app.route('/delete_income/<int:id>')
def delete_income(id):
    income = Income.query.get_or_404(id)
    month, year = income.month, income.year
    db.session.delete(income)
    db.session.commit()
    flash('تم حذف الدخل ✅', 'info')
    return redirect(url_for('index', month=month, year=year))


@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    month, year = expense.month, expense.year
    db.session.delete(expense)
    db.session.commit()
    flash('تم حذف المصروف ✅', 'info')
    return redirect(url_for('index', month=month, year=year))


@app.route('/api/chart_data')
def chart_data():
    today = date.today()
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)

    expenses = Expense.query.filter_by(month=month, year=year).all()
    expense_by_category = {}
    for exp in expenses:
        expense_by_category[exp.category] = expense_by_category.get(exp.category, 0) + exp.amount

    cat_labels = []
    cat_values = []
    cat_colors = ['#FF6384','#36A2EB','#FFCE56','#4BC0C0','#9966FF','#FF9F40','#FF6384','#C9CBCF','#7CFC00','#FF4500']

    for i, (key, val) in enumerate(expense_by_category.items()):
        info = get_category_info(key)
        cat_labels.append(f"{info[2]} {info[1]}")
        cat_values.append(val)

    monthly_data = []
    for m in range(1, 13):
        inc = db.session.query(db.func.sum(Income.amount)).filter_by(month=m, year=year).scalar() or 0
        exp = db.session.query(db.func.sum(Expense.amount)).filter_by(month=m, year=year).scalar() or 0
        monthly_data.append({'income': inc, 'expense': exp})

    return jsonify({
        'pie': {'labels': cat_labels, 'values': cat_values, 'colors': cat_colors[:len(cat_values)]},
        'bar': {'months': ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'],
                'income': [d['income'] for d in monthly_data],
                'expense': [d['expense'] for d in monthly_data]}
    })


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', debug=True, port=port)
