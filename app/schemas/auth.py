from pydantic import BaseModel, EmailStr, Field


class CompanyAccessCode(BaseModel):
    access_code: str
    company_id: str
    company_name: str
    company_domain: str | None = None
    user_type: str
    user_type_name: str
    permissions: list[str] = Field(default_factory=list)


class UserRecord(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    provider: str = "local"


class UserTypeProfile(BaseModel):
    profile_id: str
    user_id: str
    access_code: str
    company_id: str
    company_name: str
    user_type: str
    user_type_name: str
    permissions: list[str] = Field(default_factory=list)


class AccessCodeLookupRequest(BaseModel):
    access_code: str = Field(..., min_length=1)


class AccessCodeLookupResponse(BaseModel):
    ok: bool
    company: CompanyAccessCode | None = None
    message: str


class RegisterRequest(BaseModel):
    access_code: str = Field(..., min_length=1)
    email: EmailStr
    name: str = Field(..., min_length=1)
    provider: str = "local"


class LoginRequest(BaseModel):
    email: EmailStr


class AuthResponse(BaseModel):
    ok: bool
    status: str
    token: str | None = None
    user: UserRecord | None = None
    active_profile: UserTypeProfile | None = None
    profiles: list[UserTypeProfile] = Field(default_factory=list)
    company: CompanyAccessCode | None = None
    message: str
