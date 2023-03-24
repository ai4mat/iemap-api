def get_properties_files(affiliation: str, projectName: str) -> dict:
    pipeline = [
        {"$match": {"user.affiliation": affiliation, "project.name": projectName}},
        {"$unwind": {"path": "$process.properties"}},
        {
            "$replaceRoot": {
                "newRoot": {"$mergeObjects": ["$process.properties", "$user"]}
            }
        },
    ]
    return pipeline


def get_user_projects_base_info(user_email: str, affiliation: str) -> dict:
    pipeline = [
        {
            "$match": {
                "provenance.email": user_email,
                "provenance.affiliation": affiliation,
            }
        },
        {
            "$project": {
                "_id": 0,
                "id": "$_id",
                "project_name": "$project.name",
                "date_creation": "$provenance.createdAt",
                "iemap_id": "$iemap_id",
                "experiment": "$process.isExperiment",
                "material": "$material.formula",
            }
        },
    ]
    return pipeline


def get_proj_having_file_with_given_hash(
    user_email: str, affiliation: str, hash: str
) -> dict:
    pipeline = [
        {
            "$match": {
                "provenance.email": user_email,
                "provenance.affiliation": affiliation,
                "files": {"$elemMatch": {"hash": hash}},
            }
        },
        {
            "$project": {
                "_id": 1,
                "iemap_id": 1,
                "files": {
                    "$filter": {
                        "input": "$files",
                        "as": "item",
                        "cond": {
                            "$eq": [
                                "$$item.hash",
                                hash,
                            ]
                        },
                    }
                },
            }
        },
    ]
    return pipeline


def get_proj_stats() -> dict:
    pipeline = [
        {
            "$facet": {
                "total": [{"$count": "total"}],
                "countByAffiliation": [
                    {"$group": {"_id": "$provenance.affiliation", "count": {"$sum": 1}}}
                ],
                "countByUsers": [
                    {"$group": {"_id": "$provenance.email", "count": {"$sum": 1}}}
                ],
                "countHavingFiles": [
                    {"$match": {"files": {"$exists": True}}},
                    {"$count": "total"},
                ],
                "totalFiles": [
                    {"$match": {"files": {"$exists": True}}},
                    {
                        "$project": {
                            "numfiles": {"$size": "$files"},
                            "affiliation": "$provenance.affiliation",
                        }
                    },
                    {"$group": {"_id": "$affiliation", "count": {"$sum": "$numfiles"}}},
                ],
            }
        },
        {
            "$project": {
                # "totalProj": {"$first": "$total.total"}, # this is the same as the next line, not supported in MongoDB 4
                "totalProj": {"$arrayElemAt": ["$total.total", 0]},
                "totalUsers": {"$size": "$countByAffiliation.count"},
                "countProj": {
                    "$map": {
                        "input": "$countByAffiliation",
                        "as": "cba",
                        "in": {"affiliation": "$$cba._id", "n": "$$cba.count"},
                    }
                },
                "countFiles": {
                    "$map": {
                        "input": "$totalFiles",
                        "as": "tf",
                        "in": {"affiliation": "$$tf._id", "n": "$$tf.count"},
                    }
                },
            }
        },
    ]
    return pipeline


def get_proj_stats_by_user(email: str) -> dict:
    pipeline = [
        {
            "$facet": {
                "countTotal": [{"$count": "total"}],
                "countByUser": [
                    {"$match": {"provenance.email": email}},
                    {"$count": "total"},
                ],
                "countHavingFiles": [
                    {
                        "$match": {
                            "$and": [
                                {"provenance.email": "sergio.ferlito@enea.it"},
                                {"files": {"$exists": True}},
                            ]
                        }
                    },
                    {"$count": "total"},
                ],
                "totalFiles": [
                    {
                        "$match": {
                            "$and": [
                                {"provenance.email": "sergio.ferlito@enea.it"},
                                {"files": {"$exists": True}},
                            ]
                        }
                    },
                    {"$project": {"numfiles": {"$size": "$files"}}},
                    {"$group": {"_id": None, "count": {"$sum": "$numfiles"}}},
                ],
            }
        },
        {
            "$project": {
                "total": {"$arrayElemAt": ["$countTotal.total", 0]},
                "totalByUser": {"$arrayElemAt": ["$countByUser.total", 0]},
                "totalByUserWithFile": {"$arrayElemAt": ["$countHavingFiles.total", 0]},
                "totalByUserCountFiles": {"$first": "$totalFiles.count"},
            }
        },
    ]

    return pipeline


def get_iemap_formulas_and_elements() -> dict:
    pipeline = [
        {
            "$group": {
                "_id": 0,
                "formulas": {"$addToSet": "$material.formula"},
                "elements": {"$addToSet": "$material.elements"},
            }
        },
        {
            "$project": {
                "formulas": 1,
                "all_elements": {
                    "$reduce": {
                        "input": "$elements",
                        "initialValue": [],
                        "in": {
                            "$concatArrays": [
                                "$$value",
                                {
                                    "$cond": [
                                        {"$isArray": "$$this"},
                                        "$$this",
                                        ["$$this"],
                                    ]
                                },
                            ]
                        },
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "formulas": 1,
                "unique_elements": {
                    "$setIntersection": ["$all_elements", "$all_elements"]
                },
            }
        },
    ]
    return pipeline
