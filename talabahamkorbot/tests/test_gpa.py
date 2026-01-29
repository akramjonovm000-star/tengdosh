import unittest
from services.gpa_calculator import GPACalculator

class TestGPACalculator(unittest.TestCase):

    def setUp(self):
        # Mock Subjects for testing
        self.subject_A = {
            "subject": {"id": "1", "name": "Matematika", "credit": 6},
            "overallScore": {"grade": 90}, # A (4.0)
            "semester": {"code": "11"}
        }
        self.subject_B = {
            "subject": {"id": "2", "name": "Fizika", "credit": 4},
            "overallScore": {"grade": 75}, # B (3.0)
            "semester": {"code": "11"}
        }
        
        # Failed Subject (Retake Scenario)
        self.subject_C_Fail = {
            "subject": {"id": "3", "name": "Tarix", "credit": 2},
            "overallScore": {"grade": 50}, # F (0.0)
            "semester": {"code": "11"}
        }
        # Retake success
        self.subject_C_Pass = {
            "subject": {"id": "3", "name": "Tarix", "credit": 2},
            "overallScore": {"grade": 80}, # B (3.0)
            "semester": {"code": "12"}
        }

    def test_semester_gpa_weighted(self):
        """
        Test Case 1: Simple Weighted GPA
        Math (6cr, 4.0) + Physics (4cr, 3.0)
        Total Credits: 10
        Total Points: (6*4) + (4*3) = 24 + 12 = 36
        GPA = 36 / 10 = 3.6
        """
        subjects = [self.subject_A, self.subject_B]
        result = GPACalculator.calculate_gpa(subjects)
        
        self.assertEqual(result.gpa, 3.6)
        self.assertEqual(result.total_credits, 10.0)
        self.assertEqual(len(result.subjects), 2)
        
    def test_cumulative_retake_latest(self):
        """
        Test Case 2: Cumulative with Retake (Latest Policy)
        History Failed in Sem 11 (0.0), Passed in Sem 12 (3.0)
        Latest -> Should pick Sem 12 (3.0)
        
        Subjects: Math (4.0 * 6), Physics (3.0 * 4), History (3.0 * 2)
        Total Cr: 12
        Total Pts: 24 + 12 + 6 = 42
        GPA = 42 / 12 = 3.5
        """
        all_subjects = [self.subject_A, self.subject_B, self.subject_C_Fail, self.subject_C_Pass]
        result = GPACalculator.calculate_cumulative(all_subjects, retake_policy="latest")
        
        # Verify History is passed version
        history = next(s for s in result.subjects if s.subject_id == "3")
        self.assertEqual(history.grade_point, 3.0)
        self.assertEqual(history.semester_id, "12")
        
        self.assertEqual(result.gpa, 3.5)

    def test_cumulative_retake_best(self):
        """
        Test Case 3: Retake 'Best' Policy
        Imagine a scenario where latest is worse?
        Let's add Subject D: Passed with 3.0, then retake got 2.0?
        Usually retake is to improve.
        Let's assume History was 70 (2.0) first, then retake 90 (4.0).
        Latest = 4.0. Best = 4.0.
        
        Let's make a clear diff.
        """
        subj_D1 = {
             "subject": {"id": "4", "name": "RetakeTest", "credit": 5},
             "overallScore": {"grade": 80}, # B (3.0) - Sem 11
             "semester": {"code": "11"}
        }
        subj_D2 = {
             "subject": {"id": "4", "name": "RetakeTest", "credit": 5},
             "overallScore": {"grade": 60}, # C (2.0) - Sem 12 (Worse)
             "semester": {"code": "12"}
        }
        
        subjects = [subj_D1, subj_D2]
        
        # Best Policy -> Should pick 3.0
        res_best = GPACalculator.calculate_cumulative(subjects, retake_policy="best")
        self.assertEqual(res_best.gpa, 3.0)
        
        # Latest Policy -> Should pick 2.0
        res_latest = GPACalculator.calculate_cumulative(subjects, retake_policy="latest")
        self.assertEqual(res_latest.gpa, 2.0)

    def test_edge_cases(self):
        """
        Test Case 4: Zero Credits & In Progress
        """
        subj_zero_credit = {
             "subject": {"id": "5", "name": "Sport", "credit": 0},
             "overallScore": {"grade": 100},
             "semester": {"code": "11"}
        }
        subj_in_progress = {
             "subject": {"id": "6", "name": "Kimyo", "credit": 4},
             "overallScore": {"grade": 0}, # Not graded
             "semester": {"code": "11"}
        }
        
        result = GPACalculator.calculate_gpa([subj_zero_credit, subj_in_progress])
        
        # Both should be excluded
        # Sport -> Excluded (Reason: No credits)
        # Kimyo -> Excluded (Reason: In progress)
        
        self.assertEqual(result.total_credits, 0)
        self.assertEqual(result.gpa, 0.0)
        
        sport = next(s for s in result.subjects if s.name == "Sport")
        self.assertFalse(sport.included)
        self.assertEqual(sport.reason_excluded, "No credits")

if __name__ == '__main__':
    unittest.main()
