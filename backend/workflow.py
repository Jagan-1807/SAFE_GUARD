from llama_index.core.workflow import (
    Workflow,
    Event,
    StartEvent,
    StopEvent,
    step,
)
from llama_index.core.schema import NodeWithScore
from llama_index.llms.openrouter import OpenRouter
from engine import get_index
import os
from typing import List

# Events for the workflow
class RetrieveEvent(Event):
    nodes: List[NodeWithScore]
    query: str

class GenerateEvent(Event):
    response: str
    nodes: List[NodeWithScore]
    query: str

class VerifyEvent(Event):
    is_safe: bool
    feedback: str
    response: str
    nodes: List[NodeWithScore]
    query: str

class SafeGuardWorkflow(Workflow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm = OpenRouter(
            model="google/gemini-2.5-flash",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

    @step
    async def retrieve(self, ev: StartEvent) -> RetrieveEvent:
        query = ev.get("query")
        from engine import DEMO_MODE
        
        if DEMO_MODE:
            # Fake retrieval
            return RetrieveEvent(nodes=[], query=query)
            
        index = get_index()
        retriever = index.as_retriever(similarity_top_k=3)
        nodes = retriever.retrieve(query)
        return RetrieveEvent(nodes=nodes, query=query)

    @step
    async def generate(self, ev: RetrieveEvent) -> GenerateEvent:
        from engine import DEMO_MODE
        if DEMO_MODE:
            # Mock responses based on keywords
            q = ev.query.lower()
            if "shipping" in q:
                res = "Standard shipping takes 3-5 business days. Express is available for $15."
            elif "refund" in q:
                res = "You can request a full refund within 30 days of purchase."
            else:
                res = "I am in Demo Mode because no API key was found. Please add a GOOGLE_API_KEY to see real AI capabilities!"
            return GenerateEvent(response=res, nodes=[], query=ev.query)
            
        context = "\n".join([n.get_content() for n in ev.nodes])
        prompt = (
            f"Context:\n{context}\n\n"
            f"Question: {ev.query}\n\n"
            "Based ONLY on the context provided above, answer the question accurately "
            "as a customer support agent. If the answer is not in the context, say you don't know."
        )
        response = await self.llm.acomplete(prompt)
        return GenerateEvent(response=str(response), nodes=ev.nodes, query=ev.query)

    @step
    async def verify(self, ev: GenerateEvent) -> VerifyEvent:
        from engine import DEMO_MODE
        if DEMO_MODE:
            # Simulate a "Hallucination Catch" if query mentions $10
            is_safe = "$10" not in ev.query
            feedback = "Simulated: Refined because the actual express shipping price is $15, not $10." if not is_safe else "SAFE"
            return VerifyEvent(is_safe=is_safe, feedback=feedback, response=ev.response, nodes=[], query=ev.query)
            
        context = "\n".join([n.get_content() for n in ev.nodes])
        prompt = (
            f"Context:\n{context}\n\n"
            f"Proposed Answer: {ev.response}\n\n"
            "Identify any hallucinations or facts in the answer that are NOT supported by the context. "
            "Reply with 'SAFE' if the answer is perfectly supported. Otherwise, explain the unsupported claims."
        )
        verification_result = await self.llm.acomplete(prompt)
        is_safe = "SAFE" in str(verification_result).upper()
        return VerifyEvent(is_safe=is_safe, feedback=str(verification_result), response=ev.response, nodes=ev.nodes, query=ev.query)

    @step
    async def refine(self, ev: VerifyEvent) -> StopEvent:
        if ev.is_safe:
            return StopEvent(result={"response": ev.response, "verified": True, "steps": ["Retrieved context", "Generated Answer", "Verified: Safe"]})
        
        from engine import DEMO_MODE
        if DEMO_MODE:
            res = "Refined Mock Answer: Express shipping costs $15.00."
            return StopEvent(result={"response": res, "verified": False, "steps": ["Retrieved context", "Generated Answer", "Verified: Hallucination Detected", "Refined Answer"]})

        # If not safe, refine
        context = "\n".join([n.get_content() for n in ev.nodes])
        prompt = (
            f"Context:\n{context}\n\n"
            f"Faulty Answer: {ev.response}\n\n"
            f"Feedback on flaws: {ev.feedback}\n\n"
            "Rewrite the answer to be strictly accurate based on the context. Ensure all hallucinations are removed."
        )
        refined_response = await self.llm.acomplete(prompt)
        return StopEvent(result={"response": str(refined_response), "verified": False, "steps": ["Retrieved context", "Generated Answer", "Verified: Hallucination Detected", "Refined Answer"]})

async def run_safeguard(query: str):
    workflow = SafeGuardWorkflow(timeout=60, verbose=True)
    result = await workflow.run(query=query)
    return result
