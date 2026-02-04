

async def get_linkedin_person(linkedin_profile_url: str) -> dict:
    try:
        return {"status_code": 200, "data": {}}
    except Exception as e:
        return {"status_code": 500, "data": str(e)}
    


async def get_key_value_concatenation(data):
    keys = [
        "public_identifier",
        "first_name", "last_name", "full_name", "follower_count", "occupation",
        "headline", "summary", "country", "country_full_name", "city", "state",
        "experiences", "education", "languages", "languages_and_proficiencies",
        "accomplishment_organisations", "accomplishment_publications",
        "accomplishment_honors_awards", "accomplishment_patents",
        "accomplishment_courses", "accomplishment_projects",
        "accomplishment_test_scores", "volunteer_work", "recommendations", "skills",
    ]
    
    key_value_pairs = []
    
    for key in keys:
        if key in data and data[key]:
            if key in {"education", "experiences", "volunteer_work"} and isinstance(data[key], list):  
                # Remove keys that contain "url" (case-insensitive)
                filtered_entries = [
                    {k: v for k, v in entry.items() if "url" not in k.lower()}  
                    for entry in data[key]
                ]
                key_value_pairs.append(f"{key} - {filtered_entries}")
            else:
                key_value_pairs.append(f"{key} - {data[key]}")
    
    return " ".join(key_value_pairs)