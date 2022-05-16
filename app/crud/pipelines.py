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
