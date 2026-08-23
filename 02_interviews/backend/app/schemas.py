from datetime import datetime
from pydantic import BaseModel, Field
class Login(BaseModel): email:str; password:str
class SessionIn(BaseModel): candidate_name:str=Field(min_length=1); candidate_email:str|None=None; scheduled_at:datetime; duration_minutes:int=Field(gt=0,le=1440); facilitator_id:str|None=None
class SessionOut(SessionIn): id:str; state:str; end_at:datetime|None=None
class InviteOut(BaseModel): url:str; expires_at:datetime
class ExtensionIn(BaseModel): minutes:int=Field(gt=0,le=240)
class EvaluationIn(BaseModel): scores:list[dict]; recommendation:str; overall_rating:int|None=Field(default=None,ge=1,le=5); overall_notes:str|None=None; private_notes:str|None=None
class ScorecardCategory(BaseModel): name:str; description:str
