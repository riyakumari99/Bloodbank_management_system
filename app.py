from flask import Flask, render_template, request, redirect, session, flash, Response
import mysql.connector

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="smritisinha@mysql719",
    database="bloodbank"
)
cursor = conn.cursor(dictionary=True)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form["username"]
        password=request.form["password"]

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s",(username,password))
        user=cursor.fetchone()

        if user:
            session["username"]=username
            session["role"]=user["role"]
            return redirect("/dashboard")
        else:
            flash("Invalid Login","error")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")

    cursor.execute("SELECT * FROM blood_stock")
    stock=cursor.fetchall()

    return render_template("dashboard.html",stock=stock)

# ---------------- DONOR REGISTER ----------------
@app.route("/donor_register", methods=["GET","POST"])
def donor_register():
    # 🔒 LOGIN PROTECTION
    if "username" not in session:
        flash("Please login first","error")
        return redirect("/")

    if request.method=="POST":
        name=request.form["name"]
        age=int(request.form["age"])
        gender=request.form["gender"]
        blood_group=request.form["blood_group"].strip().upper()
        contact=request.form["contact"]
        donation_date=request.form["donation_date"]

        # 🔽 ELIGIBILITY FIELDS
        weight=request.form.get("weight","yes")
        disease=request.form.get("disease","no")
        surgery=request.form.get("surgery","no")
        pregnant=request.form.get("pregnant","no")
        female_weight=request.form.get("female_weight","yes")
        female_disease=request.form.get("female_disease","no")
        female_surgery=request.form.get("female_surgery","no")
        menstruating=request.form.get("menstruating","no")

        # ✅ Blood group validation
        valid=["A+","A-","B+","B-","AB+","AB-","O+","O-"]
        if blood_group not in valid:
            flash("Invalid Blood Group","error")
            return redirect("/donor_register")

        # ❌ Male / Other eligibility
        if gender in ["Male","Other"]:
            if disease=="yes":
                flash("❌ Permanently Disqualified (Serious Disease)","error")
                return redirect("/donor_register")
            if age<18 or age>65:
                flash("❌ Temporarily Disqualified (Age must be 18–65)","error")
                return redirect("/donor_register")
            if weight=="no":
                flash("❌ Temporarily Disqualified (Weight < 50kg)","error")
                return redirect("/donor_register")
            if surgery=="yes":
                flash("❌ Temporarily Disqualified (Recent Surgery/Tattoo)","error")
                return redirect("/donor_register")

        # ❌ Female eligibility
        if gender=="Female":
            if pregnant=="yes":
                flash("❌ Temporarily Disqualified (Pregnant/Breastfeeding)","error")
                return redirect("/donor_register")
            if female_weight=="no":
                flash("❌ Temporarily Disqualified (Weight < 45kg)","error")
                return redirect("/donor_register")
            if female_disease=="yes":
                flash("❌ Permanently Disqualified (Serious Disease)","error")
                return redirect("/donor_register")
            if female_surgery=="yes":
                flash("❌ Temporarily Disqualified (Recent Surgery/Tattoo)","error")
                return redirect("/donor_register")
            if menstruating=="yes":
                flash("❌ Temporarily Disqualified (Currently Menstruating)","error")
                return redirect("/donor_register")

        # ✅ Eligible → insert donor
        cursor.execute("""
            INSERT INTO donors(name, age, gender, blood_group, contact, donation_date)
            VALUES (%s,%s,%s,%s,%s,%s)
        """,(name, age, gender, blood_group, contact, donation_date))

        # ✅ Update blood stock
        cursor.execute("""
            INSERT INTO blood_stock(blood_group, quantity)
            VALUES(%s,1)
            ON DUPLICATE KEY UPDATE quantity=quantity+1
        """,(blood_group,))

        conn.commit()
        flash("✅ Donor Added Successfully & Stock Updated","success")

    return render_template("donor_register.html")

# ---------------- DONOR HISTORY ----------------
@app.route("/donor_history")
def donor_history():
    if "username" not in session:
        return redirect("/")
    cursor.execute("SELECT * FROM donors")
    donors=cursor.fetchall()
    return render_template("donor_history.html",donors=donors)

# ---------------- DELETE DONOR ----------------
@app.route("/delete_donor/<int:id>")
def delete_donor(id):
    if session.get("role")!="Admin":
        flash("Only Admin can delete","error")
        return redirect("/donor_history")
    cursor.execute("DELETE FROM donors WHERE donor_id=%s",(id,))
    conn.commit()
    flash("Donor Deleted","success")
    return redirect("/donor_history")

# ---------------- EDIT DONOR ----------------
@app.route("/edit_donor/<int:id>",methods=["GET","POST"])
def edit_donor(id):
    if session.get("role")!="Admin":
        flash("Only Admin can edit","error")
        return redirect("/donor_history")
    if request.method=="POST":
        cursor.execute("""
            UPDATE donors 
            SET name=%s, age=%s, gender=%s, blood_group=%s, contact=%s
            WHERE donor_id=%s
        """,(request.form["name"],request.form["age"],request.form["gender"],request.form["blood_group"],request.form["contact"],id))
        conn.commit()
        flash("Donor Updated","success")
        return redirect("/donor_history")
    cursor.execute("SELECT * FROM donors WHERE donor_id=%s",(id,))
    donor=cursor.fetchone()
    return render_template("edit_donor.html",donor=donor)

# ---------------- REQUEST BLOOD ----------------
@app.route("/request_blood", methods=["GET","POST"])
def request_blood():
    if "username" not in session:
        return redirect("/")
    if request.method=="POST":
        requester_name=request.form["requester_name"]
        blood_group=request.form["blood_group"]
        quantity=request.form["quantity"]
        request_date=request.form["request_date"]

        cursor.execute("""
            INSERT INTO blood_requests(requester_name,blood_group,quantity,request_date,status)
            VALUES(%s,%s,%s,%s,'Pending')
        """,(requester_name,blood_group,quantity,request_date))
        conn.commit()
        flash("Blood Request Submitted","success")
        return redirect("/request_blood")
    return render_template("request_blood.html")

# ---------------- ISSUE BLOOD ----------------
@app.route("/issue_blood")
def issue_blood():
    if "username" not in session:
        return redirect("/")
    cursor.execute("SELECT * FROM blood_requests")
    requests=cursor.fetchall()
    return render_template("issue_blood.html",requests=requests)

@app.route("/issue/<int:id>")
def issue(id):
    cursor.execute("SELECT * FROM blood_requests WHERE request_id=%s",(id,))
    req=cursor.fetchone()
    if req and req["status"]=="Pending":
        cursor.execute("SELECT quantity FROM blood_stock WHERE blood_group=%s",(req["blood_group"],))
        stock=cursor.fetchone()
        if stock and stock["quantity"]>=req["quantity"]:
            cursor.execute("UPDATE blood_stock SET quantity=quantity-%s WHERE blood_group=%s",(req["quantity"],req["blood_group"]))
            cursor.execute("UPDATE blood_requests SET status='Completed' WHERE request_id=%s",(id,))
            conn.commit()
            flash("Blood Issued Successfully","success")
        else:
            flash("Not Enough Stock","error")
    return redirect("/issue_blood")

@app.route("/reject/<int:id>")
def reject(id):
    cursor.execute("UPDATE blood_requests SET status='Rejected' WHERE request_id=%s",(id,))
    conn.commit()
    flash("Request Rejected","error")
    return redirect("/issue_blood")

# ---------------- REPORT ----------------
@app.route("/download_report")
def report():
    cursor.execute("SELECT * FROM donors")
    donors=cursor.fetchall()
    def generate():
        yield "ID,Name,Blood Group\n"
        for d in donors:
            yield f"{d['donor_id']},{d['name']},{d['blood_group']}\n"
    return Response(generate(), headers={"Content-Disposition":"attachment; filename=report.csv"})

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__=="__main__":
    app.run(debug=True)