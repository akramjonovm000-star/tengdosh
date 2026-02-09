
import json

def analyze_universities():
    with open("uni_urls.json", "r") as f:
        data = json.load(f)
        
    items = data.get("data", [])
    total_count = len(items)
    print(f"Total Universities: {total_count}")
    
    # Analyze university_type
    type_counts = {}
    for item in items:
        # Check if type is numeric
        utype = str(item.get("university_type", "Unknown"))
        type_counts[utype] = type_counts.get(utype, 0) + 1
        
    print("\nUniversity Types:")
    for k, v in type_counts.items():
        print(f"Type {k}: {v}")

    # Analyze names for keywords
    state_keywords = ["davlat", "federal", "milliy", "republika", "akademiyasi"]
    non_state_keywords = ["xalqaro", "international", "tech", "privat", "univ"]
    
    state_count = 0
    non_state_count = 0
    
    potential_non_state = []
    potential_state = []

    for item in items:
        name_lower = item.get("name", "").lower()
        if "davlat" in name_lower or "federal" in name_lower or "milliy" in name_lower:
            state_count += 1
            potential_state.append(item.get("name"))
        else:
            non_state_count += 1
            potential_non_state.append(item.get("name"))
            
    print(f"\nPotential State (Keywords: davlat/federal/milliy): {state_count}")
    print(f"Potential Non-State/Other: {non_state_count}")
    
    print("\nSample Non-State Candidates:")
    for name in potential_non_state[:20]:
        print(f" - {name}")

    print("\nSample State Candidates:")
    for name in potential_state[:5]:
        print(f" - {name}")

if __name__ == "__main__":
    analyze_universities()
