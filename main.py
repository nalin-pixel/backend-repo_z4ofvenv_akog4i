import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import create_document, get_documents
from schemas import Event, MemberApplication, ContactMessage

app = FastAPI(title="Club Website API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Club API is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


class ClubInfo(BaseModel):
    name: str
    tagline: str
    description: str
    socials: dict


@app.get("/api/club", response_model=ClubInfo)
def get_club_info():
    return ClubInfo(
        name=os.getenv("CLUB_NAME", "Your Awesome Club"),
        tagline=os.getenv("CLUB_TAGLINE", "Connect. Create. Grow."),
        description=os.getenv(
            "CLUB_DESCRIPTION",
            "We are a community of passionate people hosting events, workshops and meetups.",
        ),
        socials={
            "instagram": os.getenv("CLUB_INSTAGRAM", "https://instagram.com"),
            "twitter": os.getenv("CLUB_TWITTER", "https://twitter.com"),
            "website": os.getenv("CLUB_WEBSITE", ""),
        },
    )


@app.get("/api/events")
def list_events(limit: Optional[int] = 20):
    try:
        docs = get_documents("event", {}, limit or 20)
        # Convert datetime to isoformat for JSON
        for d in docs:
            if isinstance(d.get("date"), datetime):
                d["date"] = d["date"].isoformat()
            # Convert ObjectId to string if present
            _id = d.get("_id")
            if _id is not None:
                d["id"] = str(_id)
                del d["_id"]
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/events")
def create_event(event: Event):
    try:
        event_id = create_document("event", event)
        return {"id": event_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/join")
def submit_member_application(application: MemberApplication):
    try:
        app_id = create_document("memberapplication", application)
        return {"id": app_id, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/contact")
def submit_contact_message(message: ContactMessage):
    try:
        msg_id = create_document("contactmessage", message)
        return {"id": msg_id, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
