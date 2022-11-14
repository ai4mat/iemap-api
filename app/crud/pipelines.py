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
