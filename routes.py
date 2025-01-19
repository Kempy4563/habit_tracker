import datetime
import uuid
from flask import Blueprint, request, redirect, url_for, render_template, current_app

pages = Blueprint(
    "habits", __name__, template_folder="templates", static_folder="static"
)


# Add a context processor function that can be accessed in html templates. This function returns a date range
# of 7 days before and after the selected date
@pages.context_processor
def add_calc_date_range():
    def date_range(start: datetime.datetime):
        dates = [start + datetime.timedelta(days=diff) for diff in range(-3, 4)]
        return dates

    return {"date_range": date_range}


def check_outstanding(habits_to_display, selected_date):
    # if there are no habits to display, return False
    if not habits_to_display:
        return False
    outstanding = True
    for habit in habits_to_display:
        habit_id = habit["_id"]
        # if any habit has not been completed on the selected date, return False
        if not current_app.db.completions.find_one({"habit": habit_id, "date": selected_date}):
            print(f"Habit '{habit['name']}' has not been completed on {selected_date}")
            outstanding = False
            break
    return outstanding


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

    habits_on_date = current_app.db.habits.find({"added": {"$lte": selected_date}}).sort("_id")

    # This will retrieve all habits that were completed on the selected_date
    completions = [
        habit["habit"] for habit in current_app.db.completions.find({"date": selected_date})
    ]

    habits_dict = dict(enumerate(habits_on_date))

    # Declare the lists
    daily_habits = []
    weekly_habits = []
    monthly_habits = []
    weekday_habits = []

    # Filter habits by frequency
    for key, value in habits_dict.items():
        if value["frequency"] == "daily":
            daily_habits.append(value)
        elif value["frequency"] == "weekly":
            weekly_habits.append(value)
        elif value["frequency"] == "monthly":
            monthly_habits.append(value)
        elif value["frequency"] == "weekdays":
            weekday_habits.append(value)


    # Only display weekly habits on the days they are scheduled to occur
    weekly_habits_to_display = []
    for habit in weekly_habits:
        if selected_date.weekday() == habit["added"].weekday():
            weekly_habits_to_display.append(habit)


    # Only display monthly habits on the days they are scheduled to occur
    monthly_habits_to_display = []
    for habit in monthly_habits:
        if selected_date.day == habit["added"].day:
            monthly_habits_to_display.append(habit)


    # Only display weekday habits on weekdays
    weekday_habits_to_display = []
    for habit in weekday_habits:
        if selected_date.weekday() < 5:  # Monday is 0, Friday is 4
            weekday_habits_to_display.append(habit)

    # Create a list of all habits to display
    habits_to_display = daily_habits + weekly_habits_to_display + monthly_habits_to_display + weekday_habits_to_display

    # Check if any habits contained in habits_to_display have not been completed on the selected date and set this to
    # True or False
    outstanding = check_outstanding(habits_to_display, selected_date)

    return render_template(
        "index.html",
        habits=habits_to_display,
        selected_date=selected_date,
        completions=completions,
        title="Habit Tracker - Home",
        outstanding=outstanding,
    )


@pages.route("/complete", methods=["POST"])
def complete():
    date_string = request.form.get("date")
    date = datetime.datetime.fromisoformat(date_string)
    habit = request.form.get("habitId")

    # Check if a completion document already exists for the given habit and date
    completion = current_app.db.completions.find_one({"date": date, "habit": habit})

    if completion:
        # Completion document already exists, so delete it to revert the habit's completion status
        current_app.db.completions.delete_one({"date": date, "habit": habit})
    else:
        # Completion document does not exist, so insert a new one to mark the habit as completed
        current_app.db.completions.insert_one({"date": date, "habit": habit})

    return redirect(url_for(".index", date=date_string))


@pages.route("/add", methods=["GET", "POST"])
def add_habit():
    date_str = request.args.get("date")
    if date_str:
        selected_date = datetime.datetime.fromisoformat(date_str)
    else:
        selected_date = today_at_midnight()

    if request.form:
        frequency = request.form.get("frequency")
        current_app.db.habits.insert_one(
            {"_id": uuid.uuid4().hex, "added": selected_date, "name": request.form.get("habit"), "frequency": frequency}
        )

    return render_template(
        "add_habit.html", title="Habit Tracker - Add Habit", selected_date=selected_date
    )


@pages.route("/delete")
def delete_habit_index():
    date_str = request.args.get("date")
    if date_str:
        selected_date = datetime.datetime.fromisoformat(date_str)
    else:
        selected_date = today_at_midnight()

    habits_on_date = current_app.db.habits.find()

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
