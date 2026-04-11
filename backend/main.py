from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from workflow import SafeGuardWorkflow
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SafeGuard AI API")

# Add CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        workflow = SafeGuardWorkflow(timeout=60, verbose=True)
        result = await workflow.run(query=request.query)
        return {
            "query": request.query,
            "response": result["response"],
            "verified": result["verified"],
            "steps": result["steps"]
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
