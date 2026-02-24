

async def get_linkedin_person(linkedin_profile_url: str) -> dict:
    try:
        return {"status_code": 200, "data": {}}
    except Exception as e:
        return {"status_code": 500, "data": str(e)}
    


async def get_key_value_concatenation(data):
    keys = [
        "fullName",
        "headline",
        "addressWithCountry",
        "about",
        "experiences",
        "skills",
        "educations",
        "licenseAndCertificates",
        "languages",
        "volunteerAndAwards",
        "publications",
        "projects",
        "honorsAndAwards",
        "firstRoleYear",
        "totalRecommendationsReceived"
        ]
    
    key_value_pairs = []
    
    for key in keys:
        if key in data and data[key]:
            if key in {"educations", "experiences", "volunteerAndAwards"} and isinstance(data[key], list):  
                filtered_entries = [
                    {k: v for k, v in entry.items() if v}  
                    for entry in data[key]
                ]
                key_value_pairs.append(f"{key} - {filtered_entries}")
            else:
                key_value_pairs.append(f"{key} - {data[key]}")
    
    return " ".join(key_value_pairs)