import sys
import tempfile
from pathlib import Path

# Add project root (for engine files) and backend dir (for ta_parser)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, File, UploadFile, Query
from pydantic import BaseModel

import distributions
from stack_manager import StackManager
from stackup_step import StackupStep
from ta_parser import parse_file

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


def _run_analysis(steps: list[StepInput], lsl: float | None, usl: float | None) -> AnalyzeResponse:
    sm = StackManager(oal_lsl=lsl, oal_usl=usl)

    for step in steps:
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


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    return _run_analysis(req.steps, req.lsl, req.usl)


@app.post("/analyze/file", response_model=AnalyzeResponse)
def analyze_file(
    file: UploadFile = File(...),
    lsl: float | None = Query(None),
    usl: float | None = Query(None),
):
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    raw_steps = parse_file(tmp_path)
    steps = [StepInput(**s) for s in raw_steps]

    return _run_analysis(steps, lsl, usl)
