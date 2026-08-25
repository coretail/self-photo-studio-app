from app.main import app

for r in app.routes:
    p = getattr(r, "path", "")
    if "sessions" in p or "confirm" in p:
        print(r.methods, p)
