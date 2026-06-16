from fastapi import FastAPI
from pydantic import BaseModel

from Agents.RAGAgent import answer_query

app = FastAPI()

class TicketRequest(BaseModel):
    ticket_number: str
    short_description: str
    product_filter: str | None = None

class TicketResponse(BaseModel):
    ticket_number: str
    answer: str
    sources: list
    chunk_count: int

@app.post("/analyze", response_model=TicketResponse)
async def analyze_ticket(request: TicketRequest):
    result = await answer_query(
        question=request.short_description,
        product_filter=request.product_filter
    )
    return TicketResponse(
        ticket_number=request.ticket_number,
        answer=result["answer"],
        sources=result["sources"],
        chunk_count=result["chunk_count"]
    )

@app.get("/health")
def health():
    return {"status": "ok"}