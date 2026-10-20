
from flask import Flask, jsonify, request, render_template_string
from datetime import datetime, timezone

app = Flask(__name__)


@app.get("/")
def home():
    return render_template_string("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Student Academic Management</title>
      <style>
        body{font-family:Arial,sans-serif;background:#f1f5f9;color:#172033;margin:0}
        header{background:#173b68;color:white;padding:28px 7%}
        main{max-width:950px;margin:28px auto;padding:0 18px}
        section{background:white;padding:22px;margin:18px 0;border-radius:12px;
        box-shadow:0 2px 10px #0001}
        table{width:100%;border-collapse:collapse}
        th,td{text-align:left;padding:12px;border-bottom:1px solid #ddd}
        input,button{padding:11px;margin:6px 4px 6px 0;border-radius:6px}
        input{border:1px solid #bbb;max-width:95%}
        button{background:#173b68;color:white;border:0;cursor:pointer}
        a{color:#1763a6}
        #result{white-space:pre-wrap}
      </style>
    </head>
    <body>
      <header>
        <h1>Student Academic Management Platform</h1>
        <p>Student records and academic marks management</p>
      </header>
      <main>
        <section>
          <h2>Students</h2>
          <table>
            <thead><tr><th>ID</th><th>Name</th><th>Course</th></tr></thead>
            <tbody id="students"><tr><td colspan="3">Loading...</td></tr></tbody>
          </table>
        </section>
        <section>
          <h2>Record Student Marks</h2>
          <form id="marksForm">
            <label>Student
              <select id="student" required>
                <option value="1">Aarav Patil (ID 1)</option>
                <option value="2">Priya Sharma (ID 2)</option>
              </select>
            </label><br>
            <label>Subject <input id="subject" required maxlength="100"
              placeholder="e.g. Mathematics"></label><br>
            <label>Score (0–100) <input id="score" type="number"
              min="0" max="100" step="any" required></label><br>
            <button type="submit">Submit Marks</button>
          </form>
          <p id="result" role="status"></p>
        </section>
        <section>
          <h2>API</h2>
          <p><a href="/api/health">Health check</a> ·
          <a href="/api/students">Students API</a></p>
        </section>
      </main>
      <script>
        fetch('/api/students').then(r=>r.json()).then(data=>{
          document.getElementById('students').innerHTML=data.students.map(s=>
            `<tr><td>${s.id}</td><td>${s.name}</td><td>${s.course}</td></tr>`
          ).join('');
        }).catch(()=>document.getElementById('students').innerText='Could not load students');

        document.getElementById('marksForm').addEventListener('submit',async e=>{
          e.preventDefault();
          const result=document.getElementById('result');
          result.textContent='Submitting...';
          try{
            const response=await fetch('/api/marks',{
              method:'POST',
              headers:{'Content-Type':'application/json'},
              body:JSON.stringify({
                student_id:Number(document.getElementById('student').value),
                subject:document.getElementById('subject').value,
                score:Number(document.getElementById('score').value)
              })
            });
            const data=await response.json();
            result.textContent=response.ok
              ? 'Success: '+data.message+'\\n'+JSON.stringify(data.record)
              : 'Error: '+data.error;
            if(response.ok)e.target.reset();
          }catch(err){result.textContent='Request failed: '+err.message}
        });
      </script>
    </body>
    </html>
    """)

students = [
    {"id": 1, "name": "Aarav Patil", "course": "AI & Data Science"},
    {"id": 2, "name": "Priya Sharma", "course": "Computer Science"},
]

marks = []


@app.get("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "student-academic-platform",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@app.get("/api/students")
def get_students():
    return jsonify({"students": students}), 200


@app.post("/api/marks")
def add_marks():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be valid JSON"}), 400

    student_id = data.get("student_id")
    subject = data.get("subject")
    score = data.get("score")

    if student_id is None or not isinstance(subject, str) or not subject.strip():
        return jsonify({
            "error": "student_id and a non-empty subject are required"
        }), 400

    if isinstance(student_id, bool) or not isinstance(student_id, int):
        return jsonify({"error": "student_id must be an integer"}), 400

    if not any(student["id"] == student_id for student in students):
        return jsonify({"error": "Student not found"}), 404

    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return jsonify({"error": "score must be a number from 0 to 100"}), 400

    if not 0 <= score <= 100:
        return jsonify({"error": "score must be between 0 and 100"}), 400

    record = {
        "student_id": student_id,
        "subject": subject.strip(),
        "score": score
    }
    marks.append(record)

    return jsonify({
        "message": "Marks recorded successfully",
        "record": record
    }), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
