import sys
import os

# Add parent directory to path to mimic service environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from services.hemis_service import HemisService
    print(f"HemisService loaded from: {HemisService.__module__}")
    import services.hemis_service as hs
    print(f"File Path: {hs.__file__}")
    
    # Check the code itself
    import inspect
    source = inspect.getsource(HemisService.start_student_survey)
    if "/student/survey-start" in source:
        print("STATUS: Code has '/student/survey-start' (CORRECT)")
    elif "/education/survey-start" in source:
        print("STATUS: Code has '/education/survey-start' (OLD/INCORRECT)")
    else:
        print("STATUS: Could not determine URL in source.")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
