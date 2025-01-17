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

    # This will retrieve all habits that were added on or before the selected_date, or habits that have
    # a frequency set to "weekly" and were added on any date.
    habits_on_date = current_app.db.habits.find({"added": {"$lte": selected_date}}).sort("_id")
    #print(list(habits_on_date))
    print(type(habits_on_date))
    habits_dict = dict(enumerate(habits_on_date))

    # Filter habits by frequency
    for habit in habits_on_date:
        print(habit)

    # Declare the lists
    daily_habits = []
    weekly_habits = []
    monthly_habits = []

    # Filter habits by frequency
    for key, value in habits_dict.items():
        if value["frequency"] == "daily":
            daily_habits.append(value)
        elif value["frequency"] == "weekly":
            weekly_habits.append(value)
        elif value["frequency"] == "monthly":
            monthly_habits.append(value)

    print(daily_habits)
    print(weekly_habits)
    print(monthly_habits)


    # Only display weekly habits on the days they are scheduled to occur
    weekly_habits_to_display = []
    for habit in weekly_habits:
        if selected_date.weekday() == habit["added"].weekday():
            weekly_habits_to_display.append(habit)

    print(f"weekly habits to display: {weekly_habits_to_display}")

    # Only display monthly habits on the days they are scheduled to occur
    monthly_habits_to_display = []
    for habit in monthly_habits:
        if selected_date.day == habit["added"].day:
            monthly_habits_to_display.append(habit)

    print(f"monthly habits to display: {monthly_habits_to_display}")


    habits_to_display = daily_habits + weekly_habits_to_display + monthly_habits_to_display
    print(f"habits to display: {habits_to_display}")

    # Get completions for the selected date
    completions = current_app.db.completions.find({"date": selected_date})

    return render_template(
        "index.html",
        habits=habits_to_display,
        selected_date=selected_date,
        completions=completions,
        title="Habit Tracker - Home",
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
        frequency = request.form.get("frequency")
        current_app.db.habits.insert_one(
            {"_id": uuid.uuid4().hex, "added": today, "name": request.form.get("habit"), "frequency": frequency}
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



