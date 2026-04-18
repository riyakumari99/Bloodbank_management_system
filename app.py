from flask import Flask, render_template, request, redirect, session, flash, Response
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- FILE SETUP ----------------
if not os.path.exists("donors.csv"):
    df = pd.DataFrame(columns=["id", "name", "blood_group", "contact"])
    df.to_csv("donors.csv", index=False)

df = pd.read_csv("donors.csv")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Simple login
        if username == "admin" and password == "admin123":
            session["username"] = username
            session["role"] = "Admin"
            return redirect("/dashboard")
        else:
            flash("Invalid Login", "error")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")

    df = pd.read_csv("donors.csv")
    stock = df["blood_group"].value_counts().to_dict()

    return render_template("dashboard.html", stock=stock)

# ---------------- DONOR REGISTER ----------------
@app.route("/donor_register", methods=["GET","POST"])
def donor_register():
    if "username" not in session:
        return redirect("/")

    if request.method == "POST":
        name = request.form["name"]
        blood_group = request.form["blood_group"].strip().upper()
        contact = request.form["contact"]

        valid = ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
        if blood_group not in valid:
            flash("Invalid Blood Group","error")
            return redirect("/donor_register")

        df = pd.read_csv("donors.csv")

        new_id = len(df) + 1
        df.loc[len(df)] = [new_id, name, blood_group, contact]
        df.to_csv("donors.csv", index=False)

        flash("Donor Added Successfully", "success")

    return render_template("donor_register.html")

# ---------------- DONOR HISTORY ----------------
@app.route("/donor_history")
def donor_history():
    if "username" not in session:
        return redirect("/")

    df = pd.read_csv("donors.csv")
    donors = df.to_dict(orient="records")

    return render_template("donor_history.html", donors=donors)

# ---------------- DELETE DONOR ----------------
@app.route("/delete_donor/<int:id>")
def delete_donor(id):
    if session.get("role") != "Admin":
        flash("Only Admin can delete","error")
        return redirect("/donor_history")

    df = pd.read_csv("donors.csv")
    df = df[df["id"] != id]
    df.to_csv("donors.csv", index=False)

    flash("Donor Deleted", "success")
    return redirect("/donor_history")

# ---------------- DOWNLOAD REPORT ----------------
@app.route("/download_report")
def report():
    df = pd.read_csv("donors.csv")

    def generate():
        yield "ID,Name,Blood Group,Contact\n"
        for _, row in df.iterrows():
            yield f"{row['id']},{row['name']},{row['blood_group']},{row['contact']}\n"

    return Response(generate(), headers={"Content-Disposition":"attachment; filename=report.csv"})

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
