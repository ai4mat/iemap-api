from __future__ import annotations
from datetime import date, datetime
from enum import Enum


from bson.objectid import ObjectId as BsonObjectId
from typing import Annotated, List, Union, Optional, Type, Tuple
import inspect
import json
from pydantic import BaseModel, SecretStr, Field, validator, create_model, EmailStr
from pydantic.class_validators import root_validator
from fastapi import Form
from uuid import uuid4
from re import findall


class ObjectIdStr(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            return BsonObjectId(v)
        except Exception:
            raise ValueError(f"{v} is not a valid ObjectId")
        return str(v)


# https://stackoverflow.com/questions/59503461/how-to-parse-objectid-in-a-pydantic-model
class PydanticObjectId(BsonObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, BsonObjectId):
            raise TypeError("ObjectId required")
        return str(v)


class Provenance(BaseModel):
    email: Optional[str]  # email retrieved from JWT
    affiliation: Optional[str]  # affiliation retrieved from JWT
    createdAt: Annotated[
        datetime, Field(default_factory=lambda: datetime.now().utcnow())
    ]
    updatedAt: Annotated[
        datetime, Field(default_factory=lambda: datetime.now().utcnow())
    ]


class Project(BaseModel):
    name: str
    label: str
    description: Optional[str]


class Parameter(BaseModel):
    name: str
    value: Union[float, str]


class Agent(BaseModel):
    name: str
    version: str


class ChemicalCompositionItem(BaseModel):
    element: str
    percentage: str


class Lattice(BaseModel):
    a: str
    b: str
    c: str
    alpha: str
    beta: str
    gamma: str


class InputMaterial(BaseModel):
    lattice: Optional[Lattice]
    sites: List[List[float]]
    species: List[str]
    cell: List[List[float]]


class OutputMaterial(BaseModel):
    lattice: Optional[Lattice]
    sites: List[List[float]]
    species: List[str]
    cell: List[List[float]]


class Material(BaseModel):
    formula: str
    elements: Optional[List[str]]  # List[Union[str, str]]
    input: Optional[InputMaterial]
    output: Optional[OutputMaterial]

    @validator("elements", always=True)
    def composite_name(cls, v, values, **kwargs):
        elements = [
            x
            for x in findall("[A-Z][a-z]?|[0-9]+", values["formula"])
            if not x.isnumeric()
        ]
        return elements


class PropertyFile(BaseModel):
    fullpath: str


class Property(BaseModel):
    name: str
    value: Union[float, str]
    file: Optional[PropertyFile]


class Process(BaseModel):
    isExperiment: bool
    method: str
    agent: Optional[Agent]


# class Publication(BaseModel):
#     name: str
#     date: datetime
#     url: Optional[str]

#     class Config:
#         validate_assignment = True

#     @validator("date", pre=True, always=True)
#     def _set_publication_date_type(cls, date: datetime):
#         result = datetime.strptime(date, "%Y-%m-%d") or date
#         return result


class fileType(Enum):
    Code = "Code"
    Tabular = "Tabular"
    Image = "Image"
    Raw_Inst_Data = "Raw Instrument Data"

    @staticmethod
    def from_str(label):
        if label in "code":
            return fileType.Code
        if label in "tabular":
            return fileType.Tabular
        if label in "image":
            return fileType.Image
        if label in "raw inst data":
            return fileType.Raw_Inst_Data
        else:
            raise NotImplementedError


class FileProject(BaseModel):
    hash: Optional[str]
    # description: str
    name: str
    extention: str
    # type: fileType
    # isProcessed: bool
    size: Optional[str]
    createdAt: Annotated[
        datetime, Field(default_factory=lambda: datetime.now().utcnow())
    ]
    updatedAt: Annotated[
        datetime, Field(default_factory=lambda: datetime.now().utcnow())
    ]

    class Config:
        use_enum_values = True


def validate_datetime(cls, values):
    """
    Reusable validator for pydantic models
    """
    return values or datetime.now().utcnow()


class newProject(BaseModel):
    identifier: Optional[str]
    iemap_id: str=None 
    provenance: Optional[Provenance]
    project: Project
    process: Process
    material: Material
    parameters: List[Parameter]
    properties: List[Property]
    # files: Optional[List[FileProject]] = None
    _v: Optional[str] = Field(default="1_0")

    # this define a default value for iemap_id if not provided
    # alternatively use Field with default_factory or PrivateAttr with default_factory
    @validator("iemap_id", pre=True, always=True)
    def set_id(cls, v):
        return v or "iemap-" + str(uuid4())[:6]

    class Config:
        validate_assignment = True
        # arbitrary_types_allowed = True


class newProjectResponse(BaseModel):
    inserted_id: PydanticObjectId


class Parameters(Parameter):
    files: Optional[List[FileProject]]


class Properties(Property):
    file: Optional[str]


class ProvenanceNoEmail(Provenance):
    email: Optional[SecretStr]


class ProjectQueryResult(BaseModel):
    identifier: Optional[str]
    iemap_id: Optional[str]
    provenance: Optional[ProvenanceNoEmail]
    project: Optional[Project]
    process: Optional[Process]
    material: Optional[Material]
    parameters: Optional[List[Parameters]]
    properties: Optional[List[Properties]]
    files: Optional[List[FileProject]]


# Put your query arguments in this dict
query_params = {
    "id": (str, None),
    "fields_output": (str, "all"),
    "affiliation": (str, None),
    "project_name": (str, None),
    "provenance_email": (EmailStr, None),
    "publication_dates": (str, None),
    "date_publication": (datetime, None),
    "material_formula": (str, None),
    "material_all_elements": (str, None),
    "material_any_element": (str, None),
    "iemap_id": (str, None),
    "isExperiment": (bool, None),
    "simulationCode": (str, None),
    "experimentInstrument": (str, None),
    "simulationMethod": (str, None),
    "experimentMethod": (str, None),
    "parameterName": (str, None),
    "parameterValue": (Union[str, float], None),
    "propertyName": (str, None),
    "propertyValue": (Union[str, float], None),
    "fields": (str, None),
}

queryModel = create_model("Query", **query_params)

# def as_form(cls: Type[BaseModel]):
#     new_parameters = []

#     for field_name, model_field in cls.__fields__.items():
#         model_field: ModelField  # type: ignore

#         new_parameters.append(
#             inspect.Parameter(
#                 model_field.alias,
#                 inspect.Parameter.POSITIONAL_ONLY,
#                 default=Form(...)
#                 if not model_field.required
#                 else Form(model_field.default),
#                 annotation=model_field.outer_type_,
#             )
#         )

#     async def as_form_func(**data):
#         return cls(**data)

#     sig = inspect.signature(as_form_func)
#     sig = sig.replace(parameters=new_parameters)
#     as_form_func.__signature__ = sig  # type: ignore
#     setattr(cls, "as_form", as_form_func)
#     return cls


class userProjectsResponse(BaseModel):
    id:PydanticObjectId
    iemap_id:str
    project_name: str
    date_creation: datetime
    experiment: bool
    material: str


def as_form(cls: Type[BaseModel]):
    new_parameters = []

    for field_name, model_field in cls.__fields__.items():
        model_field: ModelField  # type: ignore

        if not model_field.required:
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Form(model_field.default),
                    annotation=model_field.outer_type_,
                )
            )
        else:
            new_parameters.append(
                inspect.Parameter(
                    model_field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=Form(...),
                    annotation=model_field.outer_type_,
                )
            )

    async def as_form_func(**data):
        return cls(**data)

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    setattr(cls, "as_form", as_form_func)
    return cls


@as_form
class PropertyForm(BaseModel):
    name: str
    type: str
    axis_labelX: str
    axis_labelY: str
    value: float
    units_x: str
    units_y: str
    isCalculated: bool
    isPhysical: bool


@as_form
class ProjectFileForm(BaseModel):
    name: str
    description: str
    type: str
    isProcessed: str
    publication_name: Optional[str] = ""
    publication_date: Optional[str] = None
    publication_url: Optional[str] = ""

    # class Config:
    #     validate_assignment = True

    # @validator("publication_date", pre=True, always=True)
    # def _set_publication_date_type(cls, publication_date: datetime):
    #     return publication_date.to or datetime(publication_date)


# https://stackoverflow.com/questions/63616798/pydantic-how-to-pass-the-default-value-to-a-variable-if-none-was-passed
# https://github.com/samuelcolvin/pydantic/issues/1593

if __name__ == "__main__":

    # TEST Model
    p = Process.parse_obj(
        {
            "isExperiment": True,
            "method": "PCA",
            "agent": {"name": "expresso", "version": "1.05"},
        }
    )
    i = InputMaterial.parse_obj(
        {
            "lattice": {
                "a": "11.050",
                "b": "10365",
                "c": "5.635",
                "alpha": "81.59",
                "beta": "68.114",
                "gamma": "30296",
            },
            "sites": "[ [x1,y1,z1], [x2, y2, z2], [x3, y3, z3] ]",
            "species": "[H,H,H]",
        }
    )
    o = OutputMaterial.parse_obj(
        {
            "lattice": {
                "a": "11.050",
                "b": "10365",
                "c": "5.635",
                "alpha": "81.59",
                "beta": "68.114",
                "gamma": "30296",
            },
            "sites": "[ [x1,y1,z1], [x2, y2, z2], [x3, y3, z3] ]",
            "species": "[H,H,H]",
        }
    )
    m = Material.parse_obj(
        {
            "formula": "C6H12O6",
            "input": {
                "lattice": {
                    "a": "11.050",
                    "b": "10365",
                    "c": "5.635",
                    "alpha": "81.59",
                    "beta": "68.114",
                    "gamma": "30296",
                },
                "sites": "[ [x1,y1,z1], [x2, y2, z2], [x3, y3, z3] ]",
                "species": "[H,H,H]",
            },
        }
    )
    par1 = Parameter.parse_obj({"name": "temperature", "value": 25.7})
    par2 = Parameter.parse_obj({"name": "type-crystal", "value": "type1"})

    prop1 = Property.parse_obj({"name": "property1", "value": "value1"})
    prop2 = Property.parse_obj({"name": "property2", "value": 700})
    prov = Provenance.parse_obj({"email": "iemap_user@enea.it", "affiliation": "enea"})
    proj = Project.parse_obj({"name": "Battery-LiOn", "label": "PB"})

    newP = newProject(
        identifier="IDAD4008",
        provenance=prov,
        material=m,
        project=proj,
        process=p,
        properties=[prop1, prop2],
        parameters=[par1, par2],
    )

    data = newProject.parse_obj(
        {
            "identifier": "IDAD4008",
            "project": {"name": "Battery-LiOn", "label": "PB"},
            "process": {
                "isExperiment": "true",
                "method": "PCA",
                "agent": {"name": "expresso", "version": "1.05"},
            },
            "material": {
                "formula": "C6H12O6",
                "input": {
                    "lattice": {
                        "a": "11.050",
                        "b": "10365",
                        "c": "5.635",
                        "alpha": "81.59",
                        "beta": "68.114",
                        "gamma": "30296",
                    },
                    "sites": "[ [x1,y1,z1], [x2, y2, z2], [x3, y3, z3] ]",
                    "species": "[H,H,H]",
                },
                "output": {
                    "lattice": {
                        "a": "11.050",
                        "b": "10365",
                        "c": "5.635",
                        "alpha": "81.59",
                        "beta": "68.114",
                        "gamma": "30296",
                    },
                    "sites": "[ [x1,y1,z1], [x2, y2, z2], [x3, y3, z3] ]",
                    "species": "[H,H,H]",
                },
            },
            "parameters": [
                {"name": "temperature", "value": 25.7},
                {"name": "type-crystal", "value": "type1"},
            ],
            "properties": [
                {"name": "property1", "value": "value1"},
                {"name": "numeric_pro", "value": 22.58},
            ],
        }
    )
    r = newProjectResponse(inserted_id=BsonObjectId("6332b8dc49c3d848c0bf288d"))

    print(r)
    print(m)
    print(i)
    print(o)
    print(p)
    print(par1)
    print(par2)
    print(prop1)
    print(prop2)
    print(proj)
    print(prov)
    print(json.dumps(json.loads(data.json()), indent=4))
