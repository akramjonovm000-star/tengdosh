import json

def analyze():
    try:
        with open('/var/www/docs.json', 'r') as f:
            data = json.load(f)
        
        paths = data.get('paths', {})
        attendance_count = paths.get('/v1/data/student-absence-count', {})
        attendance_stat = paths.get('/v1/data/attendance-stat', {})
        
        print("ABSENCE COUNT (Ref):")
        print(json.dumps(attendance_count, indent=2))

        print("\nATTENDANCE STAT PARAMS:")
        print(json.dumps(attendance_stat, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze()
