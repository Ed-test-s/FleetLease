from pydantic import BaseModel, Field


class AboutHero(BaseModel):
    title: str = Field(default="", max_length=300)
    subtitle: str = Field(default="", max_length=2000)
    image_url: str | None = Field(default=None, max_length=2048)


class AboutBlock(BaseModel):
    title: str = Field(default="", max_length=300)
    body: str = Field(default="", max_length=20000)
    image_url: str | None = Field(default=None, max_length=2048)


class AboutPageContent(BaseModel):
    hero: AboutHero = Field(default_factory=AboutHero)
    blocks: list[AboutBlock] = Field(default_factory=list, max_length=10)


class AboutImageUploadOut(BaseModel):
    url: str
