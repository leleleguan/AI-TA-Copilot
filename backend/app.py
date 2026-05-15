import sys
from pathlib import Path

# Add project root so Python can find the original engine files
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from pydantic import BaseModel

import distributions
from stack_manager import StackManager
from stackup_step import StackupStep

app = FastAPI(title="AI TA Copilot")


class StepInput(BaseModel):
    name: str
    distribution: str = "normal"
    mean: float = 0.0
    tol_plus: float = 0.0
    tol_minus: float = 0.0


class AnalyzeRequest(BaseModel):
    steps: list[StepInput]
    lsl: float | None = None
    usl: float | None = None


class AnalyzeResponse(BaseModel):
    mean: float
    std: float
    cpk: float | None
    percent_ok: float | None
    percent_nok: float | None


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    sm = StackManager(oal_lsl=req.lsl, oal_usl=req.usl)

    for step in req.steps:
        std = step.tol_plus / 3.0
        dist = distributions.Normal(mean=step.mean, std=std)
        s = StackupStep(part_name=step.name, distribution=dist, one_d_stack=True)
        sm.add_part(s)

    sm.calculate_stack()
    lengths = sm.calc_oal_dist()
    summary = sm.get_summary_data(lengths)

    return AnalyzeResponse(
        mean=summary.mean,
        std=summary.std,
        cpk=summary.cpk,
        percent_ok=summary.percent_ok,
        percent_nok=summary.percent_nok,
    )
