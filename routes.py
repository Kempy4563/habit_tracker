import datetime
import uuid
from flask import Blueprint, request, redirect, url_for, render_template, current_app

pages = Blueprint(
    "habits", __name__, template_folder="templates", static_folder="static"
)


@pages.context_processor
def add_calc_date_range():
    def date_range(start: datetime.datetime):
        dates = [start + datetime.timedelta(days=diff) for diff in range(-3, 4)]
        return dates

    return {"date_range": date_range}


def today_at_midnight():
    today = datetime.datetime.today()
    return datetime.datetime(today.year, today.month, today.day)


@pages.route("/")
def index():
    date_str = request.args.get("date")
    if date_str:
        selected_date = datetime.datetime.fromisoformat(date_str)
    else:
        selected_date = today_at_midnight()

    print("Selected date:", selected_date)

    habits_on_date = current_app.db.habits.find({"added": {"$lte": selected_date}})
    print("Habits on date:", habits_on_date)

    habits_on_date_list = list(habits_on_date)
    print("Habits on date list:", habits_on_date_list)

    completions = [
        habit["habit"]
        for habit in current_app.db.completions.find({"date": selected_date})
    ]

    # show "all habits completed" message only if the selected date is the current date
    if selected_date == today_at_midnight():
        all_habits_completed = all(habit["_id"] in completions for habit in habits_on_date_list)
    else:
        all_habits_completed = False

    print("all_habits_completed:", all_habits_completed)

    return render_template(
        "index.html",
        habits=habits_on_date_list,
        selected_date=selected_date,
        completions=completions,
        title="Habit Tracker - Home",
        all_habits_completed=all_habits_completed,
    )


@pages.route("/complete", methods=["POST"])
def complete():
    date_string = request.form.get("date")
    date = datetime.datetime.fromisoformat(date_string)
    habit = request.form.get("habitId")
    current_app.db.completions.insert_one({"date": date, "habit": habit})

    return redirect(url_for(".index", date=date_string))


@pages.route("/add", methods=["GET", "POST"])
def add_habit():
    today = today_at_midnight()

    if request.form:
        current_app.db.habits.insert_one(
            {"_id": uuid.uuid4().hex, "added": today, "name": request.form.get("habit")}
        )

    return render_template(
        "add_habit.html", title="Habit Tracker - Add Habit", selected_date=today
    )

@pages.route("/delete")
def delete_habit_index():
    date_str = request.args.get("date")
    if date_str:
        selected_date = datetime.datetime.fromisoformat(date_str)
    else:
        selected_date = today_at_midnight()

    habits_on_date = current_app.db.habits.find({"added": {"$lte": selected_date}})

    return render_template(
        "delete.html",
        habits=habits_on_date,
        selected_date=selected_date,
        title="Habit Tracker - Home",
    )

@pages.route("/delete_habit", methods=["POST"])
def delete_habit():
    print("delete_habit function called")
    print(request.form)
    habit_id = request.form.get("habitId")
    print(habit_id)
    current_app.db.habits.delete_one({"_id": habit_id})

    return redirect(url_for(".delete_habit_index"))



